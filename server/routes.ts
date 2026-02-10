import type { Express, Request, Response, NextFunction } from "express";
import { createServer, type Server } from "http";
import multer from "multer";
import bcrypt from "bcryptjs";
import { storage } from "./storage";
import { processZipFile, generateCodeSummary } from "./code-processor";
import { generateExportPackage } from "./export-generator";
import {
  ObjectStorageService,
  ObjectNotFoundError,
} from "./objectStorage";
import {
  insertProjectSchema,
  insertSoftwareInfoSchema,
  insertPatentInfoSchema,
  insertTrademarkInfoSchema,
  insertCodeBundleSchema,
  insertManualBundleSchema,
  insertProofAssetSchema,
  type ProjectType,
} from "@shared/schema";
import { z } from "zod";

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 100 * 1024 * 1024 },
});

const registerSchema = z.object({
  username: z.string().min(2, "用户名长度为2-30个字符").max(30, "用户名长度为2-30个字符"),
  password: z.string().min(6, "密码长度不能少于6个字符"),
  displayName: z.string().optional(),
});

const loginSchema = z.object({
  username: z.string().min(1, "用户名不能为空"),
  password: z.string().min(1, "密码不能为空"),
});

function requireAuth(req: Request, res: Response, next: NextFunction) {
  if (!req.session.userId) {
    return res.status(401).json({ error: "未登录，请先登录" });
  }
  next();
}

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  // === Auth API ===
  app.post("/api/auth/register", async (req, res) => {
    try {
      const parsed = registerSchema.safeParse(req.body);
      if (!parsed.success) {
        const firstError = parsed.error.errors[0]?.message || "输入验证失败";
        return res.status(400).json({ error: firstError });
      }
      const { username, password, displayName } = parsed.data;
      const existing = await storage.getUserByUsername(username);
      if (existing) {
        return res.status(409).json({ error: "用户名已存在" });
      }
      const hashedPassword = await bcrypt.hash(password, 10);
      const user = await storage.createUser({
        username,
        password: hashedPassword,
        displayName: displayName || username,
      });
      req.session.userId = user.id;
      const { password: _, ...safeUser } = user;
      res.status(201).json(safeUser);
    } catch (error) {
      console.error("Registration error:", error);
      res.status(500).json({ error: "注册失败，请稍后重试" });
    }
  });

  app.post("/api/auth/login", async (req, res) => {
    try {
      const parsed = loginSchema.safeParse(req.body);
      if (!parsed.success) {
        const firstError = parsed.error.errors[0]?.message || "输入验证失败";
        return res.status(400).json({ error: firstError });
      }
      const { username, password } = parsed.data;
      const user = await storage.getUserByUsername(username);
      if (!user) {
        return res.status(401).json({ error: "用户名或密码错误" });
      }
      const valid = await bcrypt.compare(password, user.password);
      if (!valid) {
        return res.status(401).json({ error: "用户名或密码错误" });
      }
      req.session.userId = user.id;
      const { password: _, ...safeUser } = user;
      res.json(safeUser);
    } catch (error) {
      console.error("Login error:", error);
      res.status(500).json({ error: "登录失败，请稍后重试" });
    }
  });

  app.post("/api/auth/logout", (req, res) => {
    req.session.destroy((err) => {
      if (err) {
        return res.status(500).json({ error: "登出失败" });
      }
      res.clearCookie("connect.sid");
      res.json({ message: "已登出" });
    });
  });

  app.get("/api/auth/me", async (req, res) => {
    if (!req.session.userId) {
      return res.status(401).json({ error: "未登录" });
    }
    try {
      const user = await storage.getUser(req.session.userId);
      if (!user) {
        return res.status(401).json({ error: "用户不存在" });
      }
      const { password: _, ...safeUser } = user;
      res.json(safeUser);
    } catch (error) {
      console.error("Get user error:", error);
      res.status(500).json({ error: "获取用户信息失败" });
    }
  });

  // === User Settings API ===
  app.patch("/api/auth/profile", requireAuth, async (req, res) => {
    try {
      const schema = z.object({
        displayName: z.string().min(1, "昵称不能为空").max(30, "昵称最多30个字符"),
      });
      const parsed = schema.safeParse(req.body);
      if (!parsed.success) {
        return res.status(400).json({ error: parsed.error.errors[0]?.message || "输入验证失败" });
      }
      const user = await storage.updateUser(req.session.userId!, { displayName: parsed.data.displayName });
      if (!user) {
        return res.status(404).json({ error: "用户不存在" });
      }
      const { password: _, ...safeUser } = user;
      res.json(safeUser);
    } catch (error) {
      console.error("Update profile error:", error);
      res.status(500).json({ error: "更新个人信息失败" });
    }
  });

  app.post("/api/auth/change-password", requireAuth, async (req, res) => {
    try {
      const schema = z.object({
        currentPassword: z.string().min(1, "请输入当前密码"),
        newPassword: z.string().min(6, "新密码长度不能少于6个字符"),
      });
      const parsed = schema.safeParse(req.body);
      if (!parsed.success) {
        return res.status(400).json({ error: parsed.error.errors[0]?.message || "输入验证失败" });
      }
      const user = await storage.getUser(req.session.userId!);
      if (!user) {
        return res.status(404).json({ error: "用户不存在" });
      }
      const valid = await bcrypt.compare(parsed.data.currentPassword, user.password);
      if (!valid) {
        return res.status(400).json({ error: "当前密码不正确" });
      }
      const hashedPassword = await bcrypt.hash(parsed.data.newPassword, 10);
      await storage.updateUser(req.session.userId!, { password: hashedPassword });
      res.json({ message: "密码修改成功" });
    } catch (error) {
      console.error("Change password error:", error);
      res.status(500).json({ error: "修改密码失败" });
    }
  });

  // === Protected API routes - require authentication ===
  app.use("/api/projects", requireAuth);
  app.use("/api/software-info", requireAuth);
  app.use("/api/patent-info", requireAuth);
  app.use("/api/trademark-info", requireAuth);
  app.use("/api/code-bundles", requireAuth);
  app.use("/api/manual-bundles", requireAuth);
  app.use("/api/proof-assets", requireAuth);
  app.use("/api/compliance", requireAuth);
  app.use("/api/export", requireAuth);

  // Projects API
  app.get("/api/projects", async (req, res) => {
    try {
      const type = req.query.type as ProjectType | undefined;
      const projects = await storage.getProjects(type);
      res.json(projects);
    } catch (error) {
      console.error("Error fetching projects:", error);
      res.status(500).json({ error: "Failed to fetch projects" });
    }
  });

  app.get("/api/projects/:id", async (req, res) => {
    try {
      const project = await storage.getProject(req.params.id);
      if (!project) {
        return res.status(404).json({ error: "Project not found" });
      }
      res.json(project);
    } catch (error) {
      console.error("Error fetching project:", error);
      res.status(500).json({ error: "Failed to fetch project" });
    }
  });

  app.post("/api/projects", async (req, res) => {
    try {
      const validatedData = insertProjectSchema.parse(req.body);
      const project = await storage.createProject(validatedData);
      res.status(201).json(project);
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({ error: "Invalid project data", details: error.errors });
      }
      console.error("Error creating project:", error);
      res.status(500).json({ error: "Failed to create project" });
    }
  });

  app.patch("/api/projects/:id", async (req, res) => {
    try {
      const project = await storage.updateProject(req.params.id, req.body);
      if (!project) {
        return res.status(404).json({ error: "Project not found" });
      }
      res.json(project);
    } catch (error) {
      console.error("Error updating project:", error);
      res.status(500).json({ error: "Failed to update project" });
    }
  });

  app.delete("/api/projects/:id", async (req, res) => {
    try {
      const deleted = await storage.deleteProject(req.params.id);
      if (!deleted) {
        return res.status(404).json({ error: "Project not found" });
      }
      res.status(204).send();
    } catch (error) {
      console.error("Error deleting project:", error);
      res.status(500).json({ error: "Failed to delete project" });
    }
  });

  app.post("/api/projects/:id/duplicate", async (req, res) => {
    try {
      const duplicated = await storage.duplicateProject(req.params.id);
      if (!duplicated) {
        return res.status(404).json({ error: "Project not found" });
      }
      res.status(201).json(duplicated);
    } catch (error) {
      console.error("Error duplicating project:", error);
      res.status(500).json({ error: "Failed to duplicate project" });
    }
  });

  // Software Info API (copyright projects)
  app.get("/api/projects/:id/software-info", async (req, res) => {
    try {
      const info = await storage.getSoftwareInfo(req.params.id);
      if (!info) {
        return res.status(404).json({ error: "Software info not found" });
      }
      res.json(info);
    } catch (error) {
      console.error("Error fetching software info:", error);
      res.status(500).json({ error: "Failed to fetch software info" });
    }
  });

  app.post("/api/projects/:id/software-info", async (req, res) => {
    try {
      const existingInfo = await storage.getSoftwareInfo(req.params.id);
      
      if (existingInfo) {
        const updated = await storage.updateSoftwareInfo(req.params.id, req.body);
        return res.json(updated);
      }
      
      const validatedData = insertSoftwareInfoSchema.parse({
        ...req.body,
        projectId: req.params.id,
      });
      const info = await storage.createSoftwareInfo(validatedData);
      res.status(201).json(info);
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({ error: "Invalid software info data", details: error.errors });
      }
      console.error("Error creating/updating software info:", error);
      res.status(500).json({ error: "Failed to save software info" });
    }
  });

  // Patent Info API (patent projects)
  app.get("/api/projects/:id/patent-info", async (req, res) => {
    try {
      const info = await storage.getPatentInfo(req.params.id);
      if (!info) {
        return res.status(404).json({ error: "Patent info not found" });
      }
      res.json(info);
    } catch (error) {
      console.error("Error fetching patent info:", error);
      res.status(500).json({ error: "Failed to fetch patent info" });
    }
  });

  app.post("/api/projects/:id/patent-info", async (req, res) => {
    try {
      const existingInfo = await storage.getPatentInfo(req.params.id);
      
      if (existingInfo) {
        const updated = await storage.updatePatentInfo(req.params.id, req.body);
        return res.json(updated);
      }
      
      const validatedData = insertPatentInfoSchema.parse({
        ...req.body,
        projectId: req.params.id,
      });
      const info = await storage.createPatentInfo(validatedData);
      res.status(201).json(info);
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({ error: "Invalid patent info data", details: error.errors });
      }
      console.error("Error creating/updating patent info:", error);
      res.status(500).json({ error: "Failed to save patent info" });
    }
  });

  // Trademark Info API (trademark projects)
  app.get("/api/projects/:id/trademark-info", async (req, res) => {
    try {
      const info = await storage.getTrademarkInfo(req.params.id);
      if (!info) {
        return res.status(404).json({ error: "Trademark info not found" });
      }
      res.json(info);
    } catch (error) {
      console.error("Error fetching trademark info:", error);
      res.status(500).json({ error: "Failed to fetch trademark info" });
    }
  });

  app.post("/api/projects/:id/trademark-info", async (req, res) => {
    try {
      const existingInfo = await storage.getTrademarkInfo(req.params.id);
      
      if (existingInfo) {
        const updated = await storage.updateTrademarkInfo(req.params.id, req.body);
        return res.json(updated);
      }
      
      const validatedData = insertTrademarkInfoSchema.parse({
        ...req.body,
        projectId: req.params.id,
      });
      const info = await storage.createTrademarkInfo(validatedData);
      res.status(201).json(info);
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({ error: "Invalid trademark info data", details: error.errors });
      }
      console.error("Error creating/updating trademark info:", error);
      res.status(500).json({ error: "Failed to save trademark info" });
    }
  });

  // Code Bundles API (copyright projects)
  app.get("/api/projects/:id/code-bundles", async (req, res) => {
    try {
      const bundles = await storage.getCodeBundles(req.params.id);
      res.json(bundles);
    } catch (error) {
      console.error("Error fetching code bundles:", error);
      res.status(500).json({ error: "Failed to fetch code bundles" });
    }
  });

  app.post("/api/projects/:id/code-bundles", async (req, res) => {
    try {
      const validatedData = insertCodeBundleSchema.parse({
        ...req.body,
        projectId: req.params.id,
      });
      const bundle = await storage.createCodeBundle(validatedData);
      res.status(201).json(bundle);
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({ error: "Invalid code bundle data", details: error.errors });
      }
      console.error("Error creating code bundle:", error);
      res.status(500).json({ error: "Failed to create code bundle" });
    }
  });

  app.post("/api/projects/:id/upload-code", upload.single("file"), async (req, res) => {
    try {
      const projectId = req.params.id;
      const project = await storage.getProject(projectId);
      
      if (!project) {
        return res.status(404).json({ error: "Project not found" });
      }
      
      if (!req.file) {
        return res.status(400).json({ error: "No file uploaded" });
      }
      
      const result = processZipFile(req.file.buffer);
      const summary = generateCodeSummary(result);
      
      if (result.totalFiles === 0) {
        return res.status(400).json({ 
          error: "No code files found", 
          message: "\u672A\u627E\u5230\u4EE3\u7801\u6587\u4EF6\uFF0C\u8BF7\u786E\u4FDD ZIP \u5305\u4E2D\u5305\u542B\u6E90\u4EE3\u7801\u6587\u4EF6\uFF08\u5982 .js, .ts, .py, .java \u7B49\uFF09"
        });
      }
      
      const bundle = await storage.createCodeBundle({
        projectId,
        fileName: req.file.originalname,
        fileSize: req.file.size,
        extractedContent: result.combinedContent,
        extractedPages: result.pageCount,
        pagesData: result.pages,
        hasEnoughCode: result.hasEnoughCode,
        totalLines: result.totalLines,
        status: "processed",
      });
      
      res.status(201).json({
        bundle,
        processingResult: {
          totalFiles: result.totalFiles,
          totalLines: result.totalLines,
          pageCount: result.pageCount,
          hasEnoughCode: result.hasEnoughCode,
          warnings: result.warnings,
          fileTypes: summary.fileTypes,
          largestFiles: summary.largestFiles,
          pages: result.pages,
        },
      });
    } catch (error) {
      console.error("Error processing code upload:", error);
      res.status(500).json({ error: "Failed to process code file" });
    }
  });

  app.delete("/api/code-bundles/:id", async (req, res) => {
    try {
      const deleted = await storage.deleteCodeBundle(req.params.id);
      if (!deleted) {
        return res.status(404).json({ error: "Code bundle not found" });
      }
      res.status(204).send();
    } catch (error) {
      console.error("Error deleting code bundle:", error);
      res.status(500).json({ error: "Failed to delete code bundle" });
    }
  });

  // Manual Bundles API (copyright projects)
  app.get("/api/projects/:id/manual-bundle", async (req, res) => {
    try {
      const bundle = await storage.getManualBundle(req.params.id);
      if (!bundle) {
        return res.status(404).json({ error: "Manual bundle not found" });
      }
      res.json(bundle);
    } catch (error) {
      console.error("Error fetching manual bundle:", error);
      res.status(500).json({ error: "Failed to fetch manual bundle" });
    }
  });

  app.post("/api/projects/:id/manual-bundle", async (req, res) => {
    try {
      const existingBundle = await storage.getManualBundle(req.params.id);
      
      if (existingBundle) {
        const updated = await storage.updateManualBundle(req.params.id, req.body);
        return res.json(updated);
      }
      
      const validatedData = insertManualBundleSchema.parse({
        ...req.body,
        projectId: req.params.id,
      });
      const bundle = await storage.createManualBundle(validatedData);
      res.status(201).json(bundle);
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({ error: "Invalid manual bundle data", details: error.errors });
      }
      console.error("Error creating/updating manual bundle:", error);
      res.status(500).json({ error: "Failed to save manual bundle" });
    }
  });

  // Proof Asset Download
  app.get("/api/projects/:id/proof-assets/:assetId/download", async (req, res) => {
    try {
      const assets = await storage.getProofAssets(req.params.id);
      const asset = assets.find((a) => a.id === req.params.assetId);
      
      if (!asset) {
        return res.status(404).json({ error: "Proof asset not found" });
      }
      
      if (!asset.objectPath) {
        return res.status(404).json({ error: "File not available - metadata only" });
      }
      
      const objectStorageService = new ObjectStorageService();
      const objectFile = await objectStorageService.getObjectEntityFile(asset.objectPath);
      objectStorageService.downloadObject(objectFile, res);
    } catch (error) {
      console.error("Error downloading proof asset:", error);
      if (error instanceof ObjectNotFoundError) {
        return res.status(404).json({ error: "File not found in storage" });
      }
      return res.status(500).json({ error: "Failed to download file" });
    }
  });

  // Proof Assets API (shared across all project types)
  app.get("/api/projects/:id/proof-assets", async (req, res) => {
    try {
      const assets = await storage.getProofAssets(req.params.id);
      res.json(assets);
    } catch (error) {
      console.error("Error fetching proof assets:", error);
      res.status(500).json({ error: "Failed to fetch proof assets" });
    }
  });

  app.post("/api/projects/:id/proof-assets", upload.single("file"), async (req, res) => {
    try {
      const file = req.file;
      let objectPath: string | undefined;
      
      if (file) {
        try {
          const objectStorageService = new ObjectStorageService();
          objectPath = await objectStorageService.uploadBuffer(
            file.buffer,
            file.originalname,
            file.mimetype
          );
        } catch (uploadError) {
          console.log("Object storage not available, storing metadata only:", uploadError);
        }
      }
      
      const validatedData = insertProofAssetSchema.parse({
        ...req.body,
        projectId: req.params.id,
        fileName: file?.originalname || req.body.fileName,
        fileSize: file?.size || req.body.fileSize || 0,
        objectPath: objectPath,
      });
      const asset = await storage.createProofAsset(validatedData);
      res.status(201).json(asset);
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({ error: "Invalid proof asset data", details: error.errors });
      }
      console.error("Error creating proof asset:", error);
      res.status(500).json({ error: "Failed to create proof asset" });
    }
  });

  app.delete("/api/proof-assets/:id", async (req, res) => {
    try {
      const deleted = await storage.deleteProofAsset(req.params.id);
      if (!deleted) {
        return res.status(404).json({ error: "Proof asset not found" });
      }
      res.status(204).send();
    } catch (error) {
      console.error("Error deleting proof asset:", error);
      res.status(500).json({ error: "Failed to delete proof asset" });
    }
  });

  // Compliance API (shared, type-aware)
  app.get("/api/projects/:id/compliance", async (req, res) => {
    try {
      const run = await storage.getLatestComplianceRun(req.params.id);
      if (!run) {
        return res.status(404).json({ error: "No compliance run found" });
      }
      res.json(run);
    } catch (error) {
      console.error("Error fetching compliance run:", error);
      res.status(500).json({ error: "Failed to fetch compliance run" });
    }
  });

  app.post("/api/projects/:id/compliance/run", async (req, res) => {
    try {
      const project = await storage.getProject(req.params.id);
      if (!project) {
        return res.status(404).json({ error: "Project not found" });
      }

      let results: any[] = [];

      if (project.type === "copyright") {
        results = await runCopyrightCompliance(req.params.id);
      } else if (project.type === "patent") {
        results = await runPatentCompliance(req.params.id);
      } else if (project.type === "trademark") {
        results = await runTrademarkCompliance(req.params.id);
      }

      const overallStatus = results.every((r: any) => r.status === "passed")
        ? "passed"
        : results.some((r: any) => r.status === "failed")
        ? "failed"
        : "pending";

      const run = await storage.createComplianceRun({
        projectId: req.params.id,
        results,
        overallStatus,
      });

      res.status(201).json(run);
    } catch (error) {
      console.error("Error running compliance check:", error);
      res.status(500).json({ error: "Failed to run compliance check" });
    }
  });

  // Export API
  app.get("/api/projects/:id/exports", async (req, res) => {
    try {
      const packages = await storage.getExportPackages(req.params.id);
      res.json(packages);
    } catch (error) {
      console.error("Error fetching export packages:", error);
      res.status(500).json({ error: "Failed to fetch export packages" });
    }
  });

  app.post("/api/projects/:id/export", async (req, res) => {
    try {
      const project = await storage.getProject(req.params.id);
      if (!project) {
        return res.status(404).json({ error: "Project not found" });
      }

      const exportResult = await generateExportPackage(req.params.id);

      const exportPackage = await storage.createExportPackage({
        projectId: req.params.id,
        version: project.version,
        fileName: exportResult.fileName,
        fileSize: exportResult.fileSize,
      });

      await storage.updateProject(req.params.id, { status: "exported" });

      res.status(201).json({
        ...exportPackage,
        downloadReady: true,
      });
    } catch (error) {
      console.error("Error creating export package:", error);
      res.status(500).json({ error: "Failed to create export package" });
    }
  });

  app.get("/api/projects/:id/export/download", async (req, res) => {
    try {
      const project = await storage.getProject(req.params.id);
      if (!project) {
        return res.status(404).json({ error: "Project not found" });
      }

      const exportResult = await generateExportPackage(req.params.id);

      res.setHeader("Content-Type", "application/zip");
      res.setHeader("Content-Disposition", `attachment; filename*=UTF-8''${encodeURIComponent(exportResult.fileName)}`);
      res.setHeader("Content-Length", exportResult.fileSize);
      res.send(exportResult.buffer);
    } catch (error) {
      console.error("Error downloading export package:", error);
      res.status(500).json({ error: "Failed to download export package" });
    }
  });

  return httpServer;
}

// === Compliance check helpers ===

async function runCopyrightCompliance(projectId: string) {
  const softwareInfoData = await storage.getSoftwareInfo(projectId);
  const codeBundleData = await storage.getCodeBundles(projectId);
  const manualBundle = await storage.getManualBundle(projectId);
  const proofAssetData = await storage.getProofAssets(projectId);

  const results = [];

  results.push({
    ruleId: "info-name",
    ruleName: "\u8F6F\u4EF6\u540D\u79F0",
    category: "info",
    status: softwareInfoData?.fullName ? "passed" : "failed",
    message: softwareInfoData?.fullName ? "\u8F6F\u4EF6\u5168\u79F0\u5DF2\u586B\u5199" : "\u8BF7\u586B\u5199\u8F6F\u4EF6\u5168\u79F0",
  });

  results.push({
    ruleId: "info-version",
    ruleName: "\u7248\u672C\u53F7",
    category: "info",
    status: softwareInfoData?.versionNumber ? "passed" : "failed",
    message: softwareInfoData?.versionNumber ? "\u7248\u672C\u53F7\u5DF2\u586B\u5199" : "\u8BF7\u586B\u5199\u7248\u672C\u53F7",
  });

  results.push({
    ruleId: "info-language",
    ruleName: "\u5F00\u53D1\u8BED\u8A00",
    category: "info",
    status: softwareInfoData?.developmentLanguage ? "passed" : "failed",
    message: softwareInfoData?.developmentLanguage ? "\u5F00\u53D1\u8BED\u8A00\u5DF2\u586B\u5199" : "\u8BF7\u586B\u5199\u5F00\u53D1\u8BED\u8A00",
  });

  results.push({
    ruleId: "code-upload",
    ruleName: "\u6E90\u4EE3\u7801\u4E0A\u4F20",
    category: "code",
    status: codeBundleData.length > 0 ? "passed" : "pending",
    message: codeBundleData.length > 0 ? "\u6E90\u4EE3\u7801\u5DF2\u4E0A\u4F20" : "\u8BF7\u4E0A\u4F20\u6E90\u4EE3\u7801\u6587\u4EF6",
  });

  results.push({
    ruleId: "code-pages",
    ruleName: "\u9875\u6570\u8981\u6C42(60\u9875)",
    category: "code",
    status: codeBundleData.some((b) => b.extractedPages === 60) ? "passed" : "pending",
    message: "\u9700\u751F\u621060\u9875\u6E90\u4EE3\u7801",
  });

  results.push({
    ruleId: "manual-pages",
    ruleName: "\u8BF4\u660E\u4E66\u9875\u6570(\u226515\u9875)",
    category: "manual",
    status: manualBundle && (manualBundle.pageCount || 0) >= 15 ? "passed" : "pending",
    message: "\u8BF4\u660E\u4E66\u81F3\u5C1115\u9875",
  });

  const hasIdentity = proofAssetData.some((a) => a.type === "identity");
  results.push({
    ruleId: "proof-identity",
    ruleName: "\u8EAB\u4EFD\u8BC1\u660E",
    category: "proof",
    status: hasIdentity ? "passed" : "pending",
    message: hasIdentity ? "\u8EAB\u4EFD\u8BC1\u660E\u5DF2\u4E0A\u4F20" : "\u8BF7\u4E0A\u4F20\u8EAB\u4EFD\u8BC1\u660E\u6587\u4EF6",
  });

  return results;
}

async function runPatentCompliance(projectId: string) {
  const info = await storage.getPatentInfo(projectId);
  const proofAssetData = await storage.getProofAssets(projectId);

  const results = [];

  results.push({
    ruleId: "patent-title",
    ruleName: "\u53D1\u660E\u540D\u79F0",
    category: "info",
    status: info?.title ? "passed" : "failed",
    message: info?.title ? "\u53D1\u660E\u540D\u79F0\u5DF2\u586B\u5199" : "\u8BF7\u586B\u5199\u53D1\u660E\u540D\u79F0",
  });

  results.push({
    ruleId: "patent-abstract",
    ruleName: "\u6458\u8981",
    category: "info",
    status: info?.abstract ? "passed" : "failed",
    message: info?.abstract ? "\u6458\u8981\u5DF2\u586B\u5199" : "\u8BF7\u586B\u5199\u53D1\u660E\u6458\u8981",
  });

  results.push({
    ruleId: "patent-applicant",
    ruleName: "\u7533\u8BF7\u4EBA\u4FE1\u606F",
    category: "info",
    status: info?.applicantName ? "passed" : "failed",
    message: info?.applicantName ? "\u7533\u8BF7\u4EBA\u5DF2\u586B\u5199" : "\u8BF7\u586B\u5199\u7533\u8BF7\u4EBA\u4FE1\u606F",
  });

  results.push({
    ruleId: "patent-claims",
    ruleName: "\u6743\u5229\u8981\u6C42\u4E66",
    category: "claims",
    status: info?.claimsText ? "passed" : "failed",
    message: info?.claimsText ? "\u6743\u5229\u8981\u6C42\u4E66\u5DF2\u7F16\u5199" : "\u8BF7\u7F16\u5199\u6743\u5229\u8981\u6C42\u4E66",
  });

  results.push({
    ruleId: "patent-description",
    ruleName: "\u8BF4\u660E\u4E66",
    category: "description",
    status: info?.descriptionText ? "passed" : "failed",
    message: info?.descriptionText ? "\u8BF4\u660E\u4E66\u5DF2\u7F16\u5199" : "\u8BF7\u7F16\u5199\u53D1\u660E\u8BF4\u660E\u4E66",
  });

  results.push({
    ruleId: "patent-technical-field",
    ruleName: "\u6280\u672F\u9886\u57DF",
    category: "description",
    status: info?.technicalField ? "passed" : "warning",
    message: info?.technicalField ? "\u6280\u672F\u9886\u57DF\u5DF2\u586B\u5199" : "\u5EFA\u8BAE\u586B\u5199\u6280\u672F\u9886\u57DF",
  });

  const hasIdentity = proofAssetData.some((a) => a.type === "identity");
  results.push({
    ruleId: "proof-identity",
    ruleName: "\u8EAB\u4EFD\u8BC1\u660E",
    category: "proof",
    status: hasIdentity ? "passed" : "pending",
    message: hasIdentity ? "\u8EAB\u4EFD\u8BC1\u660E\u5DF2\u4E0A\u4F20" : "\u8BF7\u4E0A\u4F20\u7533\u8BF7\u4EBA\u8EAB\u4EFD\u8BC1\u660E",
  });

  return results;
}

async function runTrademarkCompliance(projectId: string) {
  const info = await storage.getTrademarkInfo(projectId);
  const proofAssetData = await storage.getProofAssets(projectId);

  const results = [];

  results.push({
    ruleId: "tm-name",
    ruleName: "\u5546\u6807\u540D\u79F0",
    category: "info",
    status: info?.trademarkName ? "passed" : "failed",
    message: info?.trademarkName ? "\u5546\u6807\u540D\u79F0\u5DF2\u586B\u5199" : "\u8BF7\u586B\u5199\u5546\u6807\u540D\u79F0",
  });

  results.push({
    ruleId: "tm-applicant",
    ruleName: "\u7533\u8BF7\u4EBA\u4FE1\u606F",
    category: "info",
    status: info?.applicantName ? "passed" : "failed",
    message: info?.applicantName ? "\u7533\u8BF7\u4EBA\u5DF2\u586B\u5199" : "\u8BF7\u586B\u5199\u7533\u8BF7\u4EBA\u4FE1\u606F",
  });

  results.push({
    ruleId: "tm-type",
    ruleName: "\u5546\u6807\u7C7B\u578B",
    category: "info",
    status: info?.trademarkType ? "passed" : "failed",
    message: info?.trademarkType ? "\u5546\u6807\u7C7B\u578B\u5DF2\u9009\u62E9" : "\u8BF7\u9009\u62E9\u5546\u6807\u7C7B\u578B",
  });

  const hasClasses = info?.niceClasses && info.niceClasses.length > 0;
  results.push({
    ruleId: "tm-classes",
    ruleName: "\u5C3C\u65AF\u5206\u7C7B",
    category: "classification",
    status: hasClasses ? "passed" : "failed",
    message: hasClasses ? `\u5DF2\u9009\u62E9 ${info!.niceClasses!.length} \u4E2A\u5206\u7C7B` : "\u8BF7\u81F3\u5C11\u9009\u62E9\u4E00\u4E2A\u5546\u54C1/\u670D\u52A1\u5206\u7C7B",
  });

  const hasImage = proofAssetData.some((a) => a.type === "trademark_image");
  results.push({
    ruleId: "tm-image",
    ruleName: "\u5546\u6807\u56FE\u6837",
    category: "proof",
    status: hasImage ? "passed" : "failed",
    message: hasImage ? "\u5546\u6807\u56FE\u6837\u5DF2\u4E0A\u4F20" : "\u8BF7\u4E0A\u4F20\u6E05\u6670\u7684\u5546\u6807\u56FE\u6837",
  });

  const hasIdentity = proofAssetData.some((a) => a.type === "identity");
  results.push({
    ruleId: "proof-identity",
    ruleName: "\u8EAB\u4EFD\u8BC1\u660E",
    category: "proof",
    status: hasIdentity ? "passed" : "pending",
    message: hasIdentity ? "\u8EAB\u4EFD\u8BC1\u660E\u5DF2\u4E0A\u4F20" : "\u8BF7\u4E0A\u4F20\u7533\u8BF7\u4EBA\u8EAB\u4EFD\u8BC1\u660E",
  });

  return results;
}

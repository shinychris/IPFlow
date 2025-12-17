import type { Express } from "express";
import { createServer, type Server } from "http";
import multer from "multer";
import { storage } from "./storage";
import { processZipFile, generateCodeSummary } from "./code-processor";
import {
  insertProjectSchema,
  insertSoftwareInfoSchema,
  insertCodeBundleSchema,
  insertManualBundleSchema,
  insertProofAssetSchema,
} from "@shared/schema";
import { z } from "zod";

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 100 * 1024 * 1024 },
});

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  // Projects API
  app.get("/api/projects", async (req, res) => {
    try {
      const projects = await storage.getProjects();
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

  // Software Info API
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
        // Update existing
        const updated = await storage.updateSoftwareInfo(req.params.id, req.body);
        return res.json(updated);
      }
      
      // Create new
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

  // Code Bundles API
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

  // Manual Bundles API
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

  // Proof Assets API
  app.get("/api/projects/:id/proof-assets", async (req, res) => {
    try {
      const assets = await storage.getProofAssets(req.params.id);
      res.json(assets);
    } catch (error) {
      console.error("Error fetching proof assets:", error);
      res.status(500).json({ error: "Failed to fetch proof assets" });
    }
  });

  app.post("/api/projects/:id/proof-assets", async (req, res) => {
    try {
      const validatedData = insertProofAssetSchema.parse({
        ...req.body,
        projectId: req.params.id,
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

  // Compliance API
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
      // Simulate compliance check
      const project = await storage.getProject(req.params.id);
      const softwareInfo = await storage.getSoftwareInfo(req.params.id);
      const codeBundles = await storage.getCodeBundles(req.params.id);
      const manualBundle = await storage.getManualBundle(req.params.id);
      const proofAssets = await storage.getProofAssets(req.params.id);

      const results = [];

      // Info checks
      results.push({
        ruleId: "info-name",
        ruleName: "软件名称",
        category: "info",
        status: softwareInfo?.fullName ? "passed" : "failed",
        message: softwareInfo?.fullName ? "软件全称已填写" : "请填写软件全称",
      });

      results.push({
        ruleId: "info-version",
        ruleName: "版本号",
        category: "info",
        status: softwareInfo?.versionNumber ? "passed" : "failed",
        message: softwareInfo?.versionNumber ? "版本号已填写" : "请填写版本号",
      });

      results.push({
        ruleId: "info-language",
        ruleName: "开发语言",
        category: "info",
        status: softwareInfo?.developmentLanguage ? "passed" : "failed",
        message: softwareInfo?.developmentLanguage ? "开发语言已填写" : "请填写开发语言",
      });

      // Code checks
      results.push({
        ruleId: "code-upload",
        ruleName: "源代码上传",
        category: "code",
        status: codeBundles.length > 0 ? "passed" : "pending",
        message: codeBundles.length > 0 ? "源代码已上传" : "请上传源代码文件",
      });

      results.push({
        ruleId: "code-pages",
        ruleName: "页数要求(60页)",
        category: "code",
        status: codeBundles.some((b) => b.extractedPages === 60) ? "passed" : "pending",
        message: "需生成60页源代码",
      });

      results.push({
        ruleId: "code-lines",
        ruleName: "每页行数(≥50行)",
        category: "code",
        status: "pending",
        message: "每页至少50行",
      });

      results.push({
        ruleId: "code-header",
        ruleName: "页眉格式",
        category: "code",
        status: "pending",
        message: "需包含软件全称+版本号",
      });

      // Manual checks
      results.push({
        ruleId: "manual-pages",
        ruleName: "说明书页数(≥15页)",
        category: "manual",
        status: manualBundle && (manualBundle.pageCount || 0) >= 15 ? "passed" : "pending",
        message: "说明书至少15页",
      });

      results.push({
        ruleId: "manual-lines",
        ruleName: "每页行数(≥30行)",
        category: "manual",
        status: "pending",
        message: "每页至少30行",
      });

      results.push({
        ruleId: "manual-toc",
        ruleName: "目录结构",
        category: "manual",
        status: manualBundle ? "passed" : "pending",
        message: "需包含完整目录",
      });

      // Proof checks
      const hasIdentity = proofAssets.some((a) => a.type === "identity");
      results.push({
        ruleId: "proof-identity",
        ruleName: "身份证明",
        category: "proof",
        status: hasIdentity ? "passed" : "pending",
        message: hasIdentity ? "身份证明已上传" : "请上传身份证明文件",
      });

      const overallStatus = results.every((r) => r.status === "passed")
        ? "passed"
        : results.some((r) => r.status === "failed")
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

      const fileName = `SoftCopyrightKit_${project.name}_${project.version}.zip`;
      const exportPackage = await storage.createExportPackage({
        projectId: req.params.id,
        version: project.version,
        fileName,
        fileSize: Math.floor(Math.random() * 5000000) + 1000000, // Simulated size
      });

      // Update project status
      await storage.updateProject(req.params.id, { status: "exported" });

      res.status(201).json(exportPackage);
    } catch (error) {
      console.error("Error creating export package:", error);
      res.status(500).json({ error: "Failed to create export package" });
    }
  });

  return httpServer;
}

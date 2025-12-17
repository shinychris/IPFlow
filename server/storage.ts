import {
  type User,
  type InsertUser,
  type Project,
  type InsertProject,
  type SoftwareInfo,
  type InsertSoftwareInfo,
  type CodeBundle,
  type InsertCodeBundle,
  type ManualBundle,
  type InsertManualBundle,
  type ProofAsset,
  type InsertProofAsset,
  type ComplianceRun,
  type InsertComplianceRun,
  type ExportPackage,
  type InsertExportPackage,
  users,
  projects,
  softwareInfo,
  codeBundles,
  manualBundles,
  proofAssets,
  complianceRuns,
  exportPackages,
} from "@shared/schema";
import { db } from "./db";
import { eq, desc } from "drizzle-orm";

export interface IStorage {
  getUser(id: string): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;

  getProjects(): Promise<Project[]>;
  getProject(id: string): Promise<Project | undefined>;
  createProject(project: InsertProject): Promise<Project>;
  updateProject(id: string, updates: Partial<Project>): Promise<Project | undefined>;
  deleteProject(id: string): Promise<boolean>;
  duplicateProject(id: string): Promise<Project | undefined>;

  getSoftwareInfo(projectId: string): Promise<SoftwareInfo | undefined>;
  createSoftwareInfo(info: InsertSoftwareInfo): Promise<SoftwareInfo>;
  updateSoftwareInfo(projectId: string, updates: Partial<SoftwareInfo>): Promise<SoftwareInfo | undefined>;

  getCodeBundles(projectId: string): Promise<CodeBundle[]>;
  createCodeBundle(bundle: InsertCodeBundle): Promise<CodeBundle>;
  updateCodeBundle(id: string, updates: Partial<CodeBundle>): Promise<CodeBundle | undefined>;
  deleteCodeBundle(id: string): Promise<boolean>;

  getManualBundle(projectId: string): Promise<ManualBundle | undefined>;
  createManualBundle(bundle: InsertManualBundle): Promise<ManualBundle>;
  updateManualBundle(projectId: string, updates: Partial<ManualBundle>): Promise<ManualBundle | undefined>;

  getProofAssets(projectId: string): Promise<ProofAsset[]>;
  createProofAsset(asset: InsertProofAsset): Promise<ProofAsset>;
  deleteProofAsset(id: string): Promise<boolean>;

  getLatestComplianceRun(projectId: string): Promise<ComplianceRun | undefined>;
  createComplianceRun(run: InsertComplianceRun): Promise<ComplianceRun>;

  getExportPackages(projectId: string): Promise<ExportPackage[]>;
  createExportPackage(pkg: InsertExportPackage): Promise<ExportPackage>;
}

export class DatabaseStorage implements IStorage {
  async getUser(id: string): Promise<User | undefined> {
    const [user] = await db.select().from(users).where(eq(users.id, id));
    return user || undefined;
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    const [user] = await db.select().from(users).where(eq(users.username, username));
    return user || undefined;
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const [user] = await db.insert(users).values(insertUser).returning();
    return user;
  }

  async getProjects(): Promise<Project[]> {
    return await db.select().from(projects).orderBy(desc(projects.updatedAt));
  }

  async getProject(id: string): Promise<Project | undefined> {
    const [project] = await db.select().from(projects).where(eq(projects.id, id));
    return project || undefined;
  }

  async createProject(insertProject: InsertProject): Promise<Project> {
    const projectData = {
      name: insertProject.name,
      version: insertProject.version || "V1.0",
      subjectType: insertProject.subjectType as "individual" | "enterprise" | "institution",
      developmentMethod: insertProject.developmentMethod as "independent" | "cooperative" | "commissioned" | "derivative",
      publicationStatus: insertProject.publicationStatus as "unpublished" | "published",
      status: (insertProject.status || "draft") as "draft" | "in_progress" | "completed" | "exported",
      currentStep: insertProject.currentStep || 1,
    };
    const [project] = await db.insert(projects).values(projectData).returning();
    return project;
  }

  async updateProject(id: string, updates: Partial<Project>): Promise<Project | undefined> {
    const [updated] = await db
      .update(projects)
      .set({ ...updates, updatedAt: new Date() })
      .where(eq(projects.id, id))
      .returning();
    return updated || undefined;
  }

  async deleteProject(id: string): Promise<boolean> {
    const result = await db.delete(projects).where(eq(projects.id, id)).returning();
    if (result.length > 0) {
      await db.delete(softwareInfo).where(eq(softwareInfo.projectId, id));
      await db.delete(codeBundles).where(eq(codeBundles.projectId, id));
      await db.delete(manualBundles).where(eq(manualBundles.projectId, id));
      await db.delete(proofAssets).where(eq(proofAssets.projectId, id));
      await db.delete(complianceRuns).where(eq(complianceRuns.projectId, id));
      await db.delete(exportPackages).where(eq(exportPackages.projectId, id));
      return true;
    }
    return false;
  }

  async duplicateProject(id: string): Promise<Project | undefined> {
    const original = await this.getProject(id);
    if (!original) return undefined;

    const versionMatch = original.version.match(/V(\d+)\.(\d+)/);
    const newVersion = versionMatch
      ? `V${versionMatch[1]}.${parseInt(versionMatch[2]) + 1}`
      : "V1.1";

    const [duplicated] = await db.insert(projects).values({
      name: `${original.name} (副本)`,
      version: newVersion,
      subjectType: original.subjectType,
      developmentMethod: original.developmentMethod,
      publicationStatus: original.publicationStatus,
      status: "draft",
      currentStep: 1,
    }).returning();

    return duplicated;
  }

  async getSoftwareInfo(projectId: string): Promise<SoftwareInfo | undefined> {
    const [info] = await db.select().from(softwareInfo).where(eq(softwareInfo.projectId, projectId));
    return info || undefined;
  }

  async createSoftwareInfo(info: InsertSoftwareInfo): Promise<SoftwareInfo> {
    const [created] = await db.insert(softwareInfo).values(info).returning();
    return created;
  }

  async updateSoftwareInfo(projectId: string, updates: Partial<SoftwareInfo>): Promise<SoftwareInfo | undefined> {
    const [updated] = await db
      .update(softwareInfo)
      .set(updates)
      .where(eq(softwareInfo.projectId, projectId))
      .returning();
    return updated || undefined;
  }

  async getCodeBundles(projectId: string): Promise<CodeBundle[]> {
    return await db.select().from(codeBundles).where(eq(codeBundles.projectId, projectId));
  }

  async createCodeBundle(bundle: InsertCodeBundle): Promise<CodeBundle> {
    const [created] = await db.insert(codeBundles).values(bundle).returning();
    return created;
  }

  async updateCodeBundle(id: string, updates: Partial<CodeBundle>): Promise<CodeBundle | undefined> {
    const [updated] = await db
      .update(codeBundles)
      .set(updates)
      .where(eq(codeBundles.id, id))
      .returning();
    return updated || undefined;
  }

  async deleteCodeBundle(id: string): Promise<boolean> {
    const result = await db.delete(codeBundles).where(eq(codeBundles.id, id)).returning();
    return result.length > 0;
  }

  async getManualBundle(projectId: string): Promise<ManualBundle | undefined> {
    const [bundle] = await db.select().from(manualBundles).where(eq(manualBundles.projectId, projectId));
    return bundle || undefined;
  }

  async createManualBundle(bundle: InsertManualBundle): Promise<ManualBundle> {
    const bundleData = {
      projectId: bundle.projectId,
      templateType: bundle.templateType as "web" | "mobile" | "algorithm" | "script" | "desktop",
      content: bundle.content,
      wordCount: bundle.wordCount,
      pageCount: bundle.pageCount,
      screenshotCount: bundle.screenshotCount,
    };
    const [created] = await db.insert(manualBundles).values(bundleData).returning();
    return created;
  }

  async updateManualBundle(projectId: string, updates: Partial<ManualBundle>): Promise<ManualBundle | undefined> {
    const [updated] = await db
      .update(manualBundles)
      .set({ ...updates, updatedAt: new Date() })
      .where(eq(manualBundles.projectId, projectId))
      .returning();
    return updated || undefined;
  }

  async getProofAssets(projectId: string): Promise<ProofAsset[]> {
    return await db.select().from(proofAssets).where(eq(proofAssets.projectId, projectId));
  }

  async createProofAsset(asset: InsertProofAsset): Promise<ProofAsset> {
    const [created] = await db.insert(proofAssets).values(asset).returning();
    return created;
  }

  async deleteProofAsset(id: string): Promise<boolean> {
    const result = await db.delete(proofAssets).where(eq(proofAssets.id, id)).returning();
    return result.length > 0;
  }

  async getLatestComplianceRun(projectId: string): Promise<ComplianceRun | undefined> {
    const [run] = await db
      .select()
      .from(complianceRuns)
      .where(eq(complianceRuns.projectId, projectId))
      .orderBy(desc(complianceRuns.checkedAt))
      .limit(1);
    return run || undefined;
  }

  async createComplianceRun(run: InsertComplianceRun): Promise<ComplianceRun> {
    const runData = {
      projectId: run.projectId,
      results: run.results as any,
      overallStatus: run.overallStatus || "pending",
    };
    const [created] = await db.insert(complianceRuns).values(runData).returning();
    return created;
  }

  async getExportPackages(projectId: string): Promise<ExportPackage[]> {
    return await db
      .select()
      .from(exportPackages)
      .where(eq(exportPackages.projectId, projectId))
      .orderBy(desc(exportPackages.createdAt));
  }

  async createExportPackage(pkg: InsertExportPackage): Promise<ExportPackage> {
    const [created] = await db.insert(exportPackages).values(pkg).returning();
    return created;
  }
}

export const storage = new DatabaseStorage();

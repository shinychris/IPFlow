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
} from "@shared/schema";
import { randomUUID } from "crypto";

export interface IStorage {
  // User operations
  getUser(id: string): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;

  // Project operations
  getProjects(): Promise<Project[]>;
  getProject(id: string): Promise<Project | undefined>;
  createProject(project: InsertProject): Promise<Project>;
  updateProject(id: string, updates: Partial<Project>): Promise<Project | undefined>;
  deleteProject(id: string): Promise<boolean>;
  duplicateProject(id: string): Promise<Project | undefined>;

  // SoftwareInfo operations
  getSoftwareInfo(projectId: string): Promise<SoftwareInfo | undefined>;
  createSoftwareInfo(info: InsertSoftwareInfo): Promise<SoftwareInfo>;
  updateSoftwareInfo(projectId: string, updates: Partial<SoftwareInfo>): Promise<SoftwareInfo | undefined>;

  // CodeBundle operations
  getCodeBundles(projectId: string): Promise<CodeBundle[]>;
  createCodeBundle(bundle: InsertCodeBundle): Promise<CodeBundle>;
  updateCodeBundle(id: string, updates: Partial<CodeBundle>): Promise<CodeBundle | undefined>;
  deleteCodeBundle(id: string): Promise<boolean>;

  // ManualBundle operations
  getManualBundle(projectId: string): Promise<ManualBundle | undefined>;
  createManualBundle(bundle: InsertManualBundle): Promise<ManualBundle>;
  updateManualBundle(projectId: string, updates: Partial<ManualBundle>): Promise<ManualBundle | undefined>;

  // ProofAsset operations
  getProofAssets(projectId: string): Promise<ProofAsset[]>;
  createProofAsset(asset: InsertProofAsset): Promise<ProofAsset>;
  deleteProofAsset(id: string): Promise<boolean>;

  // ComplianceRun operations
  getLatestComplianceRun(projectId: string): Promise<ComplianceRun | undefined>;
  createComplianceRun(run: InsertComplianceRun): Promise<ComplianceRun>;

  // ExportPackage operations
  getExportPackages(projectId: string): Promise<ExportPackage[]>;
  createExportPackage(pkg: InsertExportPackage): Promise<ExportPackage>;
}

export class MemStorage implements IStorage {
  private users: Map<string, User>;
  private projects: Map<string, Project>;
  private softwareInfos: Map<string, SoftwareInfo>;
  private codeBundles: Map<string, CodeBundle>;
  private manualBundles: Map<string, ManualBundle>;
  private proofAssets: Map<string, ProofAsset>;
  private complianceRuns: Map<string, ComplianceRun>;
  private exportPackages: Map<string, ExportPackage>;

  constructor() {
    this.users = new Map();
    this.projects = new Map();
    this.softwareInfos = new Map();
    this.codeBundles = new Map();
    this.manualBundles = new Map();
    this.proofAssets = new Map();
    this.complianceRuns = new Map();
    this.exportPackages = new Map();

    // Add sample projects for demo
    this.initializeSampleData();
  }

  private initializeSampleData() {
    const sampleProjects: Project[] = [
      {
        id: "proj-1",
        name: "智能办公管理系统",
        version: "V1.0",
        subjectType: "enterprise",
        developmentMethod: "independent",
        publicationStatus: "unpublished",
        status: "in_progress",
        currentStep: 3,
        createdAt: new Date("2024-12-10"),
        updatedAt: new Date("2024-12-15"),
      },
      {
        id: "proj-2",
        name: "在线教育平台",
        version: "V2.0",
        subjectType: "enterprise",
        developmentMethod: "cooperative",
        publicationStatus: "published",
        status: "completed",
        currentStep: 5,
        createdAt: new Date("2024-11-20"),
        updatedAt: new Date("2024-12-12"),
      },
      {
        id: "proj-3",
        name: "数据分析工具",
        version: "V1.0",
        subjectType: "individual",
        developmentMethod: "independent",
        publicationStatus: "unpublished",
        status: "draft",
        currentStep: 1,
        createdAt: new Date("2024-12-14"),
        updatedAt: new Date("2024-12-14"),
      },
    ];

    sampleProjects.forEach((project) => {
      this.projects.set(project.id, project);
    });

    // Add sample software info
    this.softwareInfos.set("proj-1", {
      id: "info-1",
      projectId: "proj-1",
      fullName: "智能办公管理系统软件",
      shortName: "智办",
      versionNumber: "V1.0",
      developmentLanguage: "TypeScript, React",
      developmentEnvironment: "Node.js 18, VS Code",
      runtimeEnvironment: "Chrome, Edge, Firefox",
      codeLineCount: 15000,
      functionalDescription: "一款面向企业的智能办公管理系统，提供任务管理、日程安排、团队协作等功能。",
      technicalFeatures: "采用React前端框架，Node.js后端，PostgreSQL数据库，支持实时协作。",
      targetDomain: "企业办公",
      completionDate: "2024-12-01",
    });
  }

  // User operations
  async getUser(id: string): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(
      (user) => user.username === username
    );
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const id = randomUUID();
    const user: User = { ...insertUser, id };
    this.users.set(id, user);
    return user;
  }

  // Project operations
  async getProjects(): Promise<Project[]> {
    return Array.from(this.projects.values()).sort((a, b) => {
      const dateA = a.updatedAt ? new Date(a.updatedAt).getTime() : 0;
      const dateB = b.updatedAt ? new Date(b.updatedAt).getTime() : 0;
      return dateB - dateA;
    });
  }

  async getProject(id: string): Promise<Project | undefined> {
    return this.projects.get(id);
  }

  async createProject(insertProject: InsertProject): Promise<Project> {
    const id = randomUUID();
    const now = new Date();
    const project: Project = {
      ...insertProject,
      id,
      status: insertProject.status || "draft",
      currentStep: insertProject.currentStep || 1,
      createdAt: now,
      updatedAt: now,
    };
    this.projects.set(id, project);
    return project;
  }

  async updateProject(id: string, updates: Partial<Project>): Promise<Project | undefined> {
    const project = this.projects.get(id);
    if (!project) return undefined;

    const updatedProject: Project = {
      ...project,
      ...updates,
      updatedAt: new Date(),
    };
    this.projects.set(id, updatedProject);
    return updatedProject;
  }

  async deleteProject(id: string): Promise<boolean> {
    if (!this.projects.has(id)) return false;
    this.projects.delete(id);
    // Also delete related data
    this.softwareInfos.delete(id);
    Array.from(this.codeBundles.values())
      .filter((b) => b.projectId === id)
      .forEach((b) => this.codeBundles.delete(b.id));
    this.manualBundles.delete(id);
    Array.from(this.proofAssets.values())
      .filter((a) => a.projectId === id)
      .forEach((a) => this.proofAssets.delete(a.id));
    return true;
  }

  async duplicateProject(id: string): Promise<Project | undefined> {
    const original = this.projects.get(id);
    if (!original) return undefined;

    const newId = randomUUID();
    const now = new Date();
    const versionMatch = original.version.match(/V(\d+)\.(\d+)/);
    const newVersion = versionMatch
      ? `V${versionMatch[1]}.${parseInt(versionMatch[2]) + 1}`
      : "V1.1";

    const duplicated: Project = {
      ...original,
      id: newId,
      name: `${original.name} (副本)`,
      version: newVersion,
      status: "draft",
      currentStep: 1,
      createdAt: now,
      updatedAt: now,
    };
    this.projects.set(newId, duplicated);
    return duplicated;
  }

  // SoftwareInfo operations
  async getSoftwareInfo(projectId: string): Promise<SoftwareInfo | undefined> {
    return this.softwareInfos.get(projectId);
  }

  async createSoftwareInfo(info: InsertSoftwareInfo): Promise<SoftwareInfo> {
    const id = randomUUID();
    const softwareInfo: SoftwareInfo = { ...info, id };
    this.softwareInfos.set(info.projectId, softwareInfo);
    return softwareInfo;
  }

  async updateSoftwareInfo(
    projectId: string,
    updates: Partial<SoftwareInfo>
  ): Promise<SoftwareInfo | undefined> {
    const existing = this.softwareInfos.get(projectId);
    if (!existing) return undefined;

    const updated: SoftwareInfo = { ...existing, ...updates };
    this.softwareInfos.set(projectId, updated);
    return updated;
  }

  // CodeBundle operations
  async getCodeBundles(projectId: string): Promise<CodeBundle[]> {
    return Array.from(this.codeBundles.values()).filter(
      (b) => b.projectId === projectId
    );
  }

  async createCodeBundle(bundle: InsertCodeBundle): Promise<CodeBundle> {
    const id = randomUUID();
    const codeBundle: CodeBundle = {
      ...bundle,
      id,
      uploadedAt: new Date(),
      processedAt: null,
    };
    this.codeBundles.set(id, codeBundle);
    return codeBundle;
  }

  async updateCodeBundle(
    id: string,
    updates: Partial<CodeBundle>
  ): Promise<CodeBundle | undefined> {
    const existing = this.codeBundles.get(id);
    if (!existing) return undefined;

    const updated: CodeBundle = { ...existing, ...updates };
    this.codeBundles.set(id, updated);
    return updated;
  }

  async deleteCodeBundle(id: string): Promise<boolean> {
    return this.codeBundles.delete(id);
  }

  // ManualBundle operations
  async getManualBundle(projectId: string): Promise<ManualBundle | undefined> {
    return this.manualBundles.get(projectId);
  }

  async createManualBundle(bundle: InsertManualBundle): Promise<ManualBundle> {
    const id = randomUUID();
    const now = new Date();
    const manualBundle: ManualBundle = {
      ...bundle,
      id,
      createdAt: now,
      updatedAt: now,
    };
    this.manualBundles.set(bundle.projectId, manualBundle);
    return manualBundle;
  }

  async updateManualBundle(
    projectId: string,
    updates: Partial<ManualBundle>
  ): Promise<ManualBundle | undefined> {
    const existing = this.manualBundles.get(projectId);
    if (!existing) return undefined;

    const updated: ManualBundle = {
      ...existing,
      ...updates,
      updatedAt: new Date(),
    };
    this.manualBundles.set(projectId, updated);
    return updated;
  }

  // ProofAsset operations
  async getProofAssets(projectId: string): Promise<ProofAsset[]> {
    return Array.from(this.proofAssets.values()).filter(
      (a) => a.projectId === projectId
    );
  }

  async createProofAsset(asset: InsertProofAsset): Promise<ProofAsset> {
    const id = randomUUID();
    const proofAsset: ProofAsset = {
      ...asset,
      id,
      uploadedAt: new Date(),
    };
    this.proofAssets.set(id, proofAsset);
    return proofAsset;
  }

  async deleteProofAsset(id: string): Promise<boolean> {
    return this.proofAssets.delete(id);
  }

  // ComplianceRun operations
  async getLatestComplianceRun(projectId: string): Promise<ComplianceRun | undefined> {
    const runs = Array.from(this.complianceRuns.values())
      .filter((r) => r.projectId === projectId)
      .sort((a, b) => {
        const dateA = a.checkedAt ? new Date(a.checkedAt).getTime() : 0;
        const dateB = b.checkedAt ? new Date(b.checkedAt).getTime() : 0;
        return dateB - dateA;
      });
    return runs[0];
  }

  async createComplianceRun(run: InsertComplianceRun): Promise<ComplianceRun> {
    const id = randomUUID();
    const complianceRun: ComplianceRun = {
      ...run,
      id,
      checkedAt: new Date(),
    };
    this.complianceRuns.set(id, complianceRun);
    return complianceRun;
  }

  // ExportPackage operations
  async getExportPackages(projectId: string): Promise<ExportPackage[]> {
    return Array.from(this.exportPackages.values())
      .filter((p) => p.projectId === projectId)
      .sort((a, b) => {
        const dateA = a.createdAt ? new Date(a.createdAt).getTime() : 0;
        const dateB = b.createdAt ? new Date(b.createdAt).getTime() : 0;
        return dateB - dateA;
      });
  }

  async createExportPackage(pkg: InsertExportPackage): Promise<ExportPackage> {
    const id = randomUUID();
    const exportPackage: ExportPackage = {
      ...pkg,
      id,
      createdAt: new Date(),
    };
    this.exportPackages.set(id, exportPackage);
    return exportPackage;
  }
}

export const storage = new MemStorage();

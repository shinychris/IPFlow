import AdmZip from "adm-zip";
import { storage } from "./storage";

interface ExportResult {
  buffer: Buffer;
  fileName: string;
  fileSize: number;
}

export async function generateExportPackage(projectId: string): Promise<ExportResult> {
  const project = await storage.getProject(projectId);
  if (!project) {
    throw new Error("Project not found");
  }

  const softwareInfo = await storage.getSoftwareInfo(projectId);
  const codeBundles = await storage.getCodeBundles(projectId);
  const manualBundle = await storage.getManualBundle(projectId);
  const proofAssets = await storage.getProofAssets(projectId);

  const zip = new AdmZip();
  const softwareName = softwareInfo?.fullName || project.name;
  const version = softwareInfo?.versionNumber || project.version;

  zip.addFile(
    "00_材料清单.txt",
    Buffer.from(generateMaterialList(project, softwareInfo, codeBundles.length > 0, !!manualBundle), "utf-8")
  );

  if (codeBundles.length > 0) {
    const latestBundle = codeBundles[codeBundles.length - 1];
    if (latestBundle.extractedContent) {
      const codeDocument = generateCodeDocument(
        latestBundle.extractedContent,
        softwareName,
        version,
        (latestBundle as any).pagesData
      );
      zip.addFile("01_源代码鉴别材料.txt", Buffer.from(codeDocument, "utf-8"));
    }
  }

  if (manualBundle && manualBundle.content) {
    const manualContent = typeof manualBundle.content === "string" 
      ? manualBundle.content 
      : JSON.stringify(manualBundle.content, null, 2);
    zip.addFile("02_操作说明书.txt", Buffer.from(manualContent, "utf-8"));
  } else {
    zip.addFile("02_操作说明书.txt", Buffer.from("操作说明书待编写\n\n请使用步骤4的编辑器完成操作说明书。", "utf-8"));
  }

  if (softwareInfo) {
    zip.addFile("03_软件信息.txt", Buffer.from(generateSoftwareInfoDoc(softwareInfo), "utf-8"));
  }

  const proofFolder = "04_证明材料/";
  zip.addFile(proofFolder, Buffer.alloc(0));
  
  if (proofAssets.length > 0) {
    let assetList = "================================================================================\n";
    assetList += "                              证明材料清单\n";
    assetList += "================================================================================\n\n";
    assetList += "以下证明材料已记录，请在提交时附上相应的原始文件：\n\n";
    
    proofAssets.forEach((asset, index) => {
      const typeLabels: Record<string, string> = {
        identity: "身份证明",
        contract: "合同/协议",
        taskbook: "任务书",
        license: "授权书",
        inheritance: "继承证明",
      };
      assetList += `${index + 1}. ${typeLabels[asset.type] || asset.type}\n`;
      assetList += `   文件名: ${asset.fileName}\n`;
      assetList += `   文件大小: ${(asset.fileSize / 1024).toFixed(1)} KB\n`;
      assetList += `   上传时间: ${asset.uploadedAt}\n\n`;
    });
    
    assetList += "================================================================================\n";
    assetList += "注意: 由于文件存储限制，原始文件需要单独准备并与本申请包一起提交。\n";
    assetList += "================================================================================\n";
    
    zip.addFile(`${proofFolder}证明材料清单.txt`, Buffer.from(assetList, "utf-8"));
  } else {
    zip.addFile(`${proofFolder}请上传证明材料.txt`, Buffer.from(
      "================================================================================\n" +
      "                              证明材料待上传\n" +
      "================================================================================\n\n" +
      "请在项目向导中上传以下证明材料：\n\n" +
      "• 身份证明 - 个人身份证复印件或企业营业执照\n" +
      "• 授权书 - 如有代理申请需提供\n" +
      "• 合同/协议 - 如有合作开发或委托开发需提供\n" +
      "• 其他相关证明材料\n\n" +
      "================================================================================\n",
      "utf-8"
    ));
  }

  zip.addFile("05_打印指南.txt", Buffer.from(generatePrintGuide(), "utf-8"));
  zip.addFile("06_网报对照表.txt", Buffer.from(generateFieldMappingGuide(softwareInfo, project), "utf-8"));

  const buffer = zip.toBuffer();
  const fileName = `软著申请包_${softwareName}_${version}.zip`;

  return {
    buffer,
    fileName,
    fileSize: buffer.length,
  };
}

function generateMaterialList(
  project: any,
  softwareInfo: any,
  hasCode: boolean,
  hasManual: boolean
): string {
  const softwareName = softwareInfo?.fullName || project.name;
  const version = softwareInfo?.versionNumber || project.version;
  
  return `================================================================================
                        软件著作权申请材料清单
================================================================================

软件名称: ${softwareName}
版本号: ${version}
申请日期: ${new Date().toLocaleDateString("zh-CN")}

================================================================================
                              材料目录
================================================================================

1. 源代码鉴别材料 (01_源代码鉴别材料.txt)
   状态: ${hasCode ? "✓ 已准备" : "○ 待准备"}
   说明: 包含源代码前30页和后30页，共60页，每页50行

2. 操作说明书 (02_操作说明书.txt)
   状态: ${hasManual ? "✓ 已准备" : "○ 待准备"}
   说明: 软件操作使用说明

3. 软件信息 (03_软件信息.txt)
   状态: ${softwareInfo ? "✓ 已准备" : "○ 待准备"}
   说明: 软件基本信息描述

4. 证明材料 (04_证明材料/)
   说明: 身份证明、授权书等证明文件

5. 打印指南 (05_打印指南.txt)
   说明: 打印规范和要求

6. 网报对照表 (06_网报对照表.txt)
   说明: 网上申报系统字段对照

================================================================================
                              注意事项
================================================================================

• 请使用 A4 纸张打印所有材料
• 源代码材料使用单面打印
• 操作说明书可使用双面打印
• 签章位置在指定页面底部

================================================================================
`;
}

function generateCodeDocument(
  content: string,
  softwareName: string,
  version: string,
  pagesData: any[] | null
): string {
  const header = `
================================================================================
                           软件源代码鉴别材料
================================================================================

软件名称: ${softwareName}
版本号: ${version}
生成日期: ${new Date().toLocaleDateString("zh-CN")}

说明: 本文档包含源代码前30页和后30页，共60页，每页50行代码。

================================================================================

`;

  if (pagesData && pagesData.length > 0) {
    let formattedContent = header;
    
    pagesData.forEach((page) => {
      const sectionLabel = page.section === "first" ? "前" : "后";
      const pageInSection = page.section === "first" ? page.pageNumber : page.pageNumber - 30;
      
      formattedContent += `
--------------------------------------------------------------------------------
第 ${page.pageNumber} 页 (${sectionLabel}部分第 ${pageInSection} 页)  |  行 ${page.lineStart}-${page.lineEnd}
--------------------------------------------------------------------------------

${page.content}

`;
    });

    return formattedContent;
  }

  return header + content;
}

function generateSoftwareInfoDoc(softwareInfo: any): string {
  return `================================================================================
                              软件基本信息
================================================================================

【软件全称】
${softwareInfo.fullName || ""}

【软件简称】
${softwareInfo.shortName || "无"}

【版本号】
${softwareInfo.versionNumber || "V1.0"}

【开发语言】
${softwareInfo.developmentLanguage || ""}

【开发环境】
${softwareInfo.developmentEnvironment || ""}

【运行环境】
${softwareInfo.runtimeEnvironment || ""}

【代码行数】
${softwareInfo.codeLineCount || 0} 行

【完成日期】
${softwareInfo.completionDate || ""}

================================================================================
                              功能描述
================================================================================

${softwareInfo.functionalDescription || "待填写"}

================================================================================
                              技术特点
================================================================================

${softwareInfo.technicalFeatures || "待填写"}

================================================================================
                              应用领域
================================================================================

${softwareInfo.targetDomain || "待填写"}

================================================================================
`;
}

function generatePrintGuide(): string {
  return `================================================================================
                           打印与装订指南
================================================================================

【纸张要求】
• 使用 A4 规格纸张 (210mm × 297mm)
• 建议使用 80g/m² 以上的优质复印纸
• 纸张颜色为白色

【打印设置】
• 页边距: 上下左右各 2.5cm
• 字体: 宋体或仿宋
• 字号: 小四号 (12pt)
• 行距: 1.5倍行距

【源代码打印要求】
• 使用单面打印
• 使用等宽字体 (如 Courier New 或仿宋)
• 代码字号可适当减小 (10pt-11pt)
• 保持行号清晰可见

【操作说明书打印要求】
• 可使用双面打印
• 图片应清晰可辨
• 截图不要有水印或广告

【装订要求】
• 使用左侧装订
• 装订边距预留 2.5cm
• 可使用骑马钉或胶装
• 材料按清单顺序排列

【签章位置】
• 签章位于指定页面右下角
• 签章应清晰、完整
• 骑缝章按要求加盖

================================================================================
                              提交材料数量
================================================================================

• 申请表: 1份 (需签字/盖章)
• 源代码鉴别材料: 1份 (60页)
• 操作说明书: 1份 (建议10页以上)
• 身份证明文件: 1份
• 其他证明材料: 按需提供

================================================================================
`;
}

function generateFieldMappingGuide(softwareInfo: any, project: any): string {
  return `================================================================================
                        网上申报系统字段对照表
================================================================================

本表用于对照填写中国版权保护中心网上申报系统字段。

================================================================================
                              软件基本信息
================================================================================

【软件全称】
系统字段: software_name
填写内容: ${softwareInfo?.fullName || project.name}

【软件简称】
系统字段: software_short_name  
填写内容: ${softwareInfo?.shortName || "无"}

【版本号】
系统字段: version_number
填写内容: ${softwareInfo?.versionNumber || project.version}

【软件类别】
系统字段: software_category
填写内容: 应用软件

【开发方式】
系统字段: development_method
填写内容: ${project.developmentMethod === "independent" ? "独立开发" : 
           project.developmentMethod === "cooperative" ? "合作开发" : 
           project.developmentMethod === "commissioned" ? "委托开发" : "其他"}

================================================================================
                              著作权人信息
================================================================================

【著作权人类型】
系统字段: owner_type
填写内容: ${project.subjectType === "individual" ? "个人" : 
           project.subjectType === "enterprise" ? "企业法人" : "其他组织"}

【著作权人名称】
系统字段: owner_name
填写内容: [请填写实际权利人名称]

【国籍/地区】
系统字段: nationality
填写内容: 中国

【证件类型】
系统字段: id_type
填写内容: ${project.subjectType === "individual" ? "身份证" : "营业执照"}

【证件号码】
系统字段: id_number
填写内容: [请填写实际证件号码]

================================================================================
                              开发信息
================================================================================

【开发完成日期】
系统字段: completion_date
填写内容: ${softwareInfo?.completionDate || "[请填写]"}

【首次发表日期】
系统字段: first_publication_date
填写内容: ${project.publicationStatus === "unpublished" ? "未发表" : "[请填写发表日期]"}

【开发环境】
系统字段: development_environment
填写内容: ${softwareInfo?.developmentEnvironment || "[请填写]"}

【运行环境】
系统字段: runtime_environment
填写内容: ${softwareInfo?.runtimeEnvironment || "[请填写]"}

【编程语言】
系统字段: programming_language
填写内容: ${softwareInfo?.developmentLanguage || "[请填写]"}

【源程序量】
系统字段: source_code_lines
填写内容: ${softwareInfo?.codeLineCount || 0} 行

================================================================================
                              功能特点
================================================================================

【主要功能】
系统字段: main_functions
填写内容: 
${softwareInfo?.functionalDescription || "[请在操作说明书中详细描述]"}

【技术特点】
系统字段: technical_features
填写内容:
${softwareInfo?.technicalFeatures || "[请填写]"}

================================================================================
                              注意事项
================================================================================

1. 网上填报时请按系统提示完成所有必填项
2. 信息应与提交的纸质材料保持一致
3. 上传文件格式通常为 PDF，请注意大小限制
4. 提交后请保存申请编号以便查询进度

================================================================================
`;
}

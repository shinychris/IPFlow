import AdmZip from 'adm-zip';
import * as path from 'path';

const CODE_EXTENSIONS = new Set([
  '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
  '.py', '.pyw',
  '.java', '.kt', '.kts', '.scala',
  '.c', '.h', '.cpp', '.hpp', '.cc', '.cxx', '.hxx',
  '.cs', '.vb',
  '.go',
  '.rs',
  '.rb', '.erb',
  '.php', '.phtml',
  '.swift', '.m', '.mm',
  '.vue', '.svelte',
  '.html', '.htm', '.css', '.scss', '.sass', '.less',
  '.sql', '.plsql',
  '.sh', '.bash', '.zsh', '.ps1', '.bat', '.cmd',
  '.xml', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg',
  '.lua', '.pl', '.pm', '.r', '.R', '.dart', '.elm', '.ex', '.exs',
  '.hs', '.lhs', '.ml', '.mli', '.fs', '.fsx', '.clj', '.cljs',
]);

const IGNORE_DIRS = new Set([
  'node_modules', '.git', '.svn', '.hg', 'dist', 'build', 'target',
  '__pycache__', '.idea', '.vscode', '.vs', 'vendor', 'bower_components',
  '.next', '.nuxt', 'out', '.cache', 'coverage', '.nyc_output',
]);

export interface ProcessedFile {
  path: string;
  content: string;
  lineCount: number;
  extension: string;
}

export interface CodePage {
  pageNumber: number;
  content: string;
  lineStart: number;
  lineEnd: number;
  section: 'first' | 'last';
}

export interface CodeProcessingResult {
  totalFiles: number;
  totalLines: number;
  processedFiles: ProcessedFile[];
  pages: CodePage[];
  combinedContent: string;
  pageCount: number;
  warnings: string[];
  hasEnoughCode: boolean;
}

function isCodeFile(filePath: string): boolean {
  const ext = path.extname(filePath).toLowerCase();
  return CODE_EXTENSIONS.has(ext);
}

function shouldIgnorePath(filePath: string): boolean {
  const parts = filePath.split(/[\\/]/);
  return parts.some(part => IGNORE_DIRS.has(part) || part.startsWith('.'));
}

function addLineNumbers(lines: string[], startLine: number = 1): string[] {
  return lines.map((line, idx) => {
    const lineNum = (startLine + idx).toString().padStart(5, ' ');
    return `${lineNum}  ${line}`;
  });
}

const LINES_PER_PAGE = 50;
const PAGES_FIRST = 30;
const PAGES_LAST = 30;
const TOTAL_REQUIRED_PAGES = PAGES_FIRST + PAGES_LAST;
const TOTAL_REQUIRED_LINES = LINES_PER_PAGE * TOTAL_REQUIRED_PAGES;

export function processZipFile(buffer: Buffer): CodeProcessingResult {
  const zip = new AdmZip(buffer);
  const entries = zip.getEntries();
  const warnings: string[] = [];
  
  const codeFiles: ProcessedFile[] = [];
  
  for (const entry of entries) {
    if (entry.isDirectory) continue;
    
    const filePath = entry.entryName;
    
    if (shouldIgnorePath(filePath)) continue;
    
    if (!isCodeFile(filePath)) continue;
    
    try {
      const content = entry.getData().toString('utf-8');
      const lineCount = content.split('\n').length;
      
      if (content.includes('\x00')) {
        continue;
      }
      
      codeFiles.push({
        path: filePath,
        content,
        lineCount,
        extension: path.extname(filePath).toLowerCase(),
      });
    } catch (err) {
      warnings.push(`Failed to process file: ${filePath}`);
    }
  }
  
  codeFiles.sort((a, b) => a.path.localeCompare(b.path));
  
  const totalFiles = codeFiles.length;
  const totalLines = codeFiles.reduce((sum, f) => sum + f.lineCount, 0);
  
  let combinedLines: string[] = [];
  
  for (const file of codeFiles) {
    combinedLines.push(`// ============================================================`);
    combinedLines.push(`// File: ${file.path}`);
    combinedLines.push(`// ============================================================`);
    combinedLines.push(...file.content.split('\n'));
    combinedLines.push('');
  }
  
  const hasEnoughCode = combinedLines.length >= TOTAL_REQUIRED_LINES;
  
  if (combinedLines.length < TOTAL_REQUIRED_LINES) {
    warnings.push(`\u4EE3\u7801\u884C\u6570\u4E0D\u8DB3\uFF1A\u9700\u8981 ${TOTAL_REQUIRED_LINES} \u884C\uFF0C\u5B9E\u9645 ${combinedLines.length} \u884C\uFF0C\u5C06\u91CD\u590D\u586B\u5145`);
    
    const originalLines = [...combinedLines];
    while (combinedLines.length < TOTAL_REQUIRED_LINES) {
      combinedLines.push('');
      combinedLines.push('// ============================================================');
      combinedLines.push('// [Repeated content to meet page requirements]');
      combinedLines.push('// ============================================================');
      for (const line of originalLines) {
        combinedLines.push(line);
        if (combinedLines.length >= TOTAL_REQUIRED_LINES) break;
      }
    }
  }
  
  const pages: CodePage[] = [];
  
  const firstSectionLines = combinedLines.slice(0, LINES_PER_PAGE * PAGES_FIRST);
  for (let i = 0; i < PAGES_FIRST; i++) {
    const startIdx = i * LINES_PER_PAGE;
    const pageLines = firstSectionLines.slice(startIdx, startIdx + LINES_PER_PAGE);
    const lineStart = startIdx + 1;
    const numberedLines = addLineNumbers(pageLines, lineStart);
    
    pages.push({
      pageNumber: i + 1,
      content: numberedLines.join('\n'),
      lineStart,
      lineEnd: lineStart + pageLines.length - 1,
      section: 'first',
    });
  }
  
  const lastSectionStart = Math.max(combinedLines.length - LINES_PER_PAGE * PAGES_LAST, LINES_PER_PAGE * PAGES_FIRST);
  const lastSectionLines = combinedLines.slice(lastSectionStart);
  
  for (let i = 0; i < PAGES_LAST; i++) {
    const startIdx = i * LINES_PER_PAGE;
    const pageLines = lastSectionLines.slice(startIdx, startIdx + LINES_PER_PAGE);
    const lineStart = lastSectionStart + startIdx + 1;
    const numberedLines = addLineNumbers(pageLines, lineStart);
    
    pages.push({
      pageNumber: PAGES_FIRST + i + 1,
      content: numberedLines.join('\n'),
      lineStart,
      lineEnd: lineStart + pageLines.length - 1,
      section: 'last',
    });
  }
  
  const firstContent = pages
    .filter(p => p.section === 'first')
    .map(p => p.content)
    .join('\n\n');
  
  const lastContent = pages
    .filter(p => p.section === 'last')
    .map(p => p.content)
    .join('\n\n');
  
  const combinedContent = firstContent + '\n\n/* ... \u4E2D\u95F4\u4EE3\u7801\u7701\u7565 ... */\n\n' + lastContent;
  
  return {
    totalFiles,
    totalLines,
    processedFiles: codeFiles,
    pages,
    combinedContent,
    pageCount: pages.length,
    warnings,
    hasEnoughCode,
  };
}

export function generateCodeSummary(result: CodeProcessingResult): {
  fileTypes: Record<string, number>;
  largestFiles: { path: string; lines: number }[];
} {
  const fileTypes: Record<string, number> = {};
  
  for (const file of result.processedFiles) {
    const ext = file.extension || 'unknown';
    fileTypes[ext] = (fileTypes[ext] || 0) + 1;
  }
  
  const largestFiles = [...result.processedFiles]
    .sort((a, b) => b.lineCount - a.lineCount)
    .slice(0, 10)
    .map(f => ({ path: f.path, lines: f.lineCount }));
  
  return { fileTypes, largestFiles };
}

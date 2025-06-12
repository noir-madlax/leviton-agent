// @babel/standalone 类型声明文件
declare module '@babel/standalone' {
  // 转换选项接口
  interface TransformOptions {
    presets?: string[] | Array<string | [string, unknown]>;
    plugins?: string[] | Array<string | [string, unknown]>;
    filename?: string;
    sourceType?: 'module' | 'script' | 'unambiguous';
    compact?: boolean | 'auto';
    minified?: boolean;
    comments?: boolean;
    env?: {
      [key: string]: TransformOptions;
    };
    retainLines?: boolean;
    sourceMaps?: boolean | 'inline' | 'both';
    sourceFileName?: string;
    sourceRoot?: string;
  }

  // 转换结果接口
  interface TransformResult {
    code?: string;
    map?: unknown;
    ast?: unknown;
  }

  // 主要的transform函数
  export function transform(code: string, options?: TransformOptions): TransformResult;

  // 其他可能用到的函数
  export function transformSync(code: string, options?: TransformOptions): TransformResult;
  export function transformAsync(code: string, options?: TransformOptions): Promise<TransformResult>;

  // 版本信息
  export const version: string;

  // 注册预设和插件的函数
  export function registerPreset(name: string, preset: unknown): void;
  export function registerPlugin(name: string, plugin: unknown): void;

  // 可用的预设和插件
  export const availablePresets: string[];
  export const availablePlugins: string[];
} 
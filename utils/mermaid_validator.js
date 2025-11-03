#!/usr/bin/env node
/**
 * Mermaid语法验证器
 * 直接使用 Mermaid.js 的解析器进行语法验证
 * 基于 mermaid-linter.js 的实现方式
 */

// 从命令行参数获取 Mermaid 代码（通过 JSON 编码传递）
let mermaidCode = '';

try {
  // 尝试从命令行参数获取（JSON 编码的字符串）
  const arg = process.argv[2];
  if (arg) {
    // 尝试解析 JSON（如果是以引号开头和结尾的字符串）
    try {
      mermaidCode = JSON.parse(arg);
    } catch (e) {
      // 解析失败，直接使用原始参数
      mermaidCode = arg;
    }
  }
} catch (e) {
  // 忽略错误，继续使用空字符串
}

if (!mermaidCode || !mermaidCode.trim()) {
  const errorResult = {
    isValid: false,
    error: '未提供Mermaid代码',
    diagramType: null
  };
  console.log(JSON.stringify(errorResult));
  process.exit(1);
}

try {
  // 导入 mermaid 库
  let mermaid;
  try {
    // 尝试使用 require (CommonJS)
    mermaid = require('mermaid');
  } catch (e) {
    // 如果 require 失败，说明 mermaid 未安装
    const errorResult = {
      isValid: false,
      error: 'Mermaid库未找到。请运行: npm install mermaid',
      diagramType: null
    };
    console.log(JSON.stringify(errorResult));
    process.exit(1);
  }
  
  // 初始化 Mermaid
  if (mermaid && typeof mermaid.initialize === 'function') {
    mermaid.initialize({ 
      startOnLoad: false,
      securityLevel: 'strict'
    });
  }
  
  // 验证代码
  const result = validateMermaidCode(mermaidCode.trim(), mermaid);
  
  // 输出 JSON 格式的结果
  console.log(JSON.stringify(result));
  
  // 根据结果设置退出码
  process.exit(result.isValid ? 0 : 1);
  
} catch (error) {
  // 错误处理
  const errorResult = {
    isValid: false,
    error: error.message || String(error),
    diagramType: null
  };
  
  console.log(JSON.stringify(errorResult));
  process.exit(1);
}

/**
 * 验证 Mermaid 代码
 * 直接使用 Mermaid.js 的 parse 方法
 */
function validateMermaidCode(code, mermaid) {
  if (!code || !code.trim()) {
    return {
      isValid: false,
      error: 'Mermaid代码为空',
      diagramType: null
    };
  }
  
  // 检测图表类型
  const firstLine = code.trim().split('\n')[0].trim();
  let diagramType = null;
  
  const diagramTypeMap = {
    'flowchart': 'flowchart',
    'graph': 'flowchart',
    'sequenceDiagram': 'sequenceDiagram',
    'classDiagram': 'classDiagram',
    'stateDiagram-v2': 'stateDiagram-v2',
    'stateDiagram': 'stateDiagram',
    'erDiagram': 'erDiagram',
    'journey': 'journey',
    'gantt': 'gantt',
    'pie': 'pie',
    'gitgraph': 'gitgraph',
    'quadrantChart': 'quadrantChart'
  };
  
  for (const [key, value] of Object.entries(diagramTypeMap)) {
    if (firstLine.toLowerCase().startsWith(key.toLowerCase())) {
      diagramType = value;
      break;
    }
  }
  
  if (!mermaid) {
    return {
      isValid: false,
      error: 'Mermaid库未找到',
      diagramType: diagramType
    };
  }
  
  try {
    // 使用 Mermaid.js 的 parse 方法进行验证
    // parse 方法会同步解析代码，如果语法错误会抛出异常
    if (mermaid.mermaidAPI && typeof mermaid.mermaidAPI.parse === 'function') {
      try {
        // 调用 parse 方法，如果成功则没有语法错误
        mermaid.mermaidAPI.parse(code);
        return {
          isValid: true,
          error: null,
          diagramType: diagramType
        };
      } catch (parseError) {
        // 捕获解析错误
        const errorMessage = parseError.message || String(parseError);
        return {
          isValid: false,
          error: errorMessage,
          diagramType: diagramType
        };
      }
    } else {
      // 如果没有 parse 方法，尝试其他方式
      // 某些版本的 mermaid 可能 API 不同
      return {
        isValid: false,
        error: 'Mermaid API不可用，请确保使用正确版本的mermaid库（>=10.0.0）',
        diagramType: diagramType
      };
    }
    
  } catch (error) {
    return {
      isValid: false,
      error: error.message || String(error),
      diagramType: diagramType
    };
  }
}


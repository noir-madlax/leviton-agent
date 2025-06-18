import { NextRequest, NextResponse } from 'next/server';

// 后端 API 配置
const BACKEND_URL = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

// 支持的 HTTP 方法
export async function GET(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxyRequest(request, params.path, 'GET');
}

export async function POST(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxyRequest(request, params.path, 'POST');
}

export async function PUT(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxyRequest(request, params.path, 'PUT');
}

export async function DELETE(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxyRequest(request, params.path, 'DELETE');
}

export async function PATCH(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxyRequest(request, params.path, 'PATCH');
}

async function proxyRequest(request: NextRequest, pathSegments: string[], method: string) {
  try {
    // 重建完整的 API 路径
    const apiPath = pathSegments.join('/');
    const backendUrl = `${BACKEND_URL}/api/${apiPath}`;
    
    // 获取查询参数
    const url = new URL(request.url);
    const searchParams = url.searchParams.toString();
    const fullBackendUrl = searchParams ? `${backendUrl}?${searchParams}` : backendUrl;

    console.log(`Proxying ${method} request to backend:`, fullBackendUrl);

    // 构建请求头
    const headers: HeadersInit = {};

    // 复制重要的头部
    const importantHeaders = [
      'content-type', 
      'authorization', 
      'user-agent', 
      'accept', 
      'accept-language',
      'accept-encoding'
    ];
    
    importantHeaders.forEach(headerName => {
      const headerValue = request.headers.get(headerName);
      if (headerValue) {
        headers[headerName] = headerValue;
      }
    });

    // 如果没有 content-type，默认设置为 application/json
    if (!headers['content-type'] && ['POST', 'PUT', 'PATCH'].includes(method)) {
      headers['content-type'] = 'application/json';
    }

    // 准备请求体（仅对有请求体的方法）
    let body: string | undefined;
    if (['POST', 'PUT', 'PATCH'].includes(method)) {
      try {
        const contentType = request.headers.get('content-type') || '';
        
        if (contentType.includes('application/json')) {
          const requestBody = await request.json();
          body = JSON.stringify(requestBody);
          console.log('Request body (JSON):', requestBody);
        } else if (contentType.includes('application/x-www-form-urlencoded') || contentType.includes('multipart/form-data')) {
          // 对于表单数据，直接传递
          body = await request.text();
          console.log('Request body (Form):', body.substring(0, 200) + '...');
        } else {
          // 其他类型，尝试作为文本处理
          body = await request.text();
          console.log('Request body (Text):', body.substring(0, 200) + '...');
        }
      } catch (error) {
        console.warn('Could not parse request body:', error);
        body = undefined;
      }
    }

    // 发送请求到后端
    const response = await fetch(fullBackendUrl, {
      method,
      headers,
      body,
      // 设置超时时间
      signal: AbortSignal.timeout(30000), // 30秒超时
    });

    console.log('Backend response status:', response.status);

    // 获取响应数据
    let responseData;
    const contentType = response.headers.get('content-type') || '';
    
    if (contentType.includes('application/json')) {
      responseData = await response.json();
      console.log('Backend response data (JSON):', responseData);
    } else if (contentType.includes('text/')) {
      responseData = await response.text();
      console.log('Backend response data (Text):', responseData.substring(0, 200) + '...');
    } else {
      // 对于二进制数据或其他类型，直接返回
      const buffer = await response.arrayBuffer();
      return new NextResponse(buffer, {
        status: response.status,
        headers: {
          'Content-Type': contentType,
          'Content-Length': buffer.byteLength.toString(),
        }
      });
    }

    // 构建响应头
    const responseHeaders: HeadersInit = {
      'Content-Type': contentType || 'application/json',
    };

    // 复制一些重要的响应头
    const responseHeadersToCopy = [
      'cache-control',
      'content-encoding',
      'content-disposition',
      'x-ratelimit-limit',
      'x-ratelimit-remaining',
      'x-ratelimit-reset'
    ];

    responseHeadersToCopy.forEach(headerName => {
      const headerValue = response.headers.get(headerName);
      if (headerValue) {
        responseHeaders[headerName] = headerValue;
      }
    });

    // 返回响应，保持原始状态码
    if (contentType.includes('application/json')) {
      return NextResponse.json(responseData, { 
        status: response.status,
        headers: responseHeaders
      });
    } else {
      return new NextResponse(responseData, {
        status: response.status,
        headers: responseHeaders
      });
    }
    
  } catch (error) {
    console.error('Proxy API error:', error);
    
    // 检查是否是超时错误
    if (error instanceof Error && error.name === 'AbortError') {
      return NextResponse.json(
        { 
          error: 'Request timeout',
          message: 'Backend request timed out after 30 seconds',
          path: pathSegments.join('/')
        },
        { status: 504 } // Gateway Timeout
      );
    }

    // 检查是否是网络连接错误
    if (error instanceof Error && (error.message.includes('ECONNREFUSED') || error.message.includes('fetch failed'))) {
      return NextResponse.json(
        { 
          error: 'Backend unavailable',
          message: 'Could not connect to backend server',
          path: pathSegments.join('/'),
          backend_url: BACKEND_URL
        },
        { status: 502 } // Bad Gateway
      );
    }
    
    return NextResponse.json(
      { 
        error: 'Internal proxy error',
        message: error instanceof Error ? error.message : 'Unknown error',
        path: pathSegments.join('/')
      },
      { status: 500 }
    );
  }
} 
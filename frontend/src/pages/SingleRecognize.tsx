import { useState } from 'react';
import { Input, Button, Card, Spin, Alert, Typography, Progress, Descriptions, Tag, Timeline, Empty } from 'antd';
import { ScanOutlined, BugOutlined, SafetyCertificateOutlined, DatabaseOutlined } from '@ant-design/icons';
import { recognize } from '../api';

const { TextArea } = Input;
const { Text } = Typography;

interface FingerprintResult {
  service: string;
  version: string | null;
  os: string | null;
  port: number | null;
  confidence: number;
  raw_banner: string;
  matched_knowledge: Array<{
    content: string;
    metadata: {
      type: string;
      title: string;
    };
  }>;
}

const typeIcons: Record<string, React.ReactNode> = {
  fingerprint: <DatabaseOutlined style={{ color: '#00d4ff' }} />,
  vulnerability: <BugOutlined style={{ color: '#ff4d4f' }} />,
  sop: <SafetyCertificateOutlined style={{ color: '#52c41a' }} />,
};

const typeColors: Record<string, string> = {
  fingerprint: 'blue',
  vulnerability: 'red',
  sop: 'green',
};

const typeLabels: Record<string, string> = {
  fingerprint: '指纹特征',
  vulnerability: '漏洞情报',
  sop: '应急SOP',
};

function JsonHighlight({ data }: { data: any }) {
  const jsonStr = JSON.stringify(data, null, 2);
  const highlighted = jsonStr
    .replace(/("(\\u[\dA-Fa-f]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+\.?\d*)/g, (match) => {
    let cls = 'json-number';
    if (/^"/.test(match)) {
      cls = /:$/.test(match) ? 'json-key' : 'json-string';
    } else if (/true|false/.test(match)) {
      cls = 'json-boolean';
    } else if (/null/.test(match)) {
      cls = 'json-null';
    }
    return `<span class="${cls}">${match}</span>`;
  });

  return (
    <pre
      className="json-highlight"
      dangerouslySetInnerHTML={{ __html: highlighted }}
    />
  );
}

export default function SingleRecognize({ backendOnline }: { backendOnline: boolean }) {
  const [banner, setBanner] = useState('');
  const [result, setResult] = useState<FingerprintResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const examples = [
    'SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.1',
    'nginx/1.24.0',
    'MyAwesomeGateway/2.0 (built on nginx)',
    'redis_version:7.2.3\nredis_mode:standalone\nos:Linux',
  ];

  const handleRecognize = async () => {
    if (!banner.trim()) {
      setError('请输入 Banner 文本');
      return;
    }
    setError('');
    setLoading(true);
    setResult(null);
    try {
      const res = await recognize(banner.trim());
      setResult(res.data);
    } catch (e: any) {
      setError(e.response?.data?.detail || '识别失败，请检查后端服务和 API Key 配置');
    }
    setLoading(false);
  };

  const confidenceColor = result
    ? result.confidence > 0.7
      ? '#52c41a'
      : result.confidence > 0.4
        ? '#faad14'
        : '#ff4d4f'
    : '#00d4ff';

  return (
    <div>
      {!backendOnline && (
        <Alert
          type="error"
          message="后端服务离线"
          description="请先启动后端服务：cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000"
          style={{ marginBottom: 16 }}
        />
      )}

      <Card className="hover-card" title={<><ScanOutlined style={{ marginRight: 8 }} />输入 Banner 文本</>} style={{ marginBottom: 16 }}>
        <TextArea
          rows={4}
          value={banner}
          placeholder="输入 Banner 文本，如 SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.1"
          onChange={(e) => setBanner(e.target.value)}
          style={{ fontFamily: 'monospace' }}
        />
        <div style={{ marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <Button
            type="primary"
            onClick={handleRecognize}
            loading={loading}
            size="large"
            icon={<ScanOutlined />}
            disabled={!backendOnline}
          >
            开始识别
          </Button>
          <Text type="secondary" style={{ lineHeight: '40px', marginRight: 16 }}>
            示例：
          </Text>
          {examples.map((ex, i) => (
            <Tag
              key={i}
              style={{ cursor: 'pointer', fontFamily: 'monospace', lineHeight: '32px' }}
              onClick={() => setBanner(ex)}
            >
              {ex.slice(0, 30)}{ex.length > 30 ? '...' : ''}
            </Tag>
          ))}
        </div>
      </Card>

      {error && (
        <Alert type="error" message={error} style={{ marginBottom: 16 }} />
      )}

      {loading && (
        <Card style={{ textAlign: 'center', padding: 48 }}>
          <Spin size="large" tip="正在调用 LLM 识别指纹..." />
        </Card>
      )}

      {result && (
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          {/* 左侧：指纹结果 */}
          <div style={{ flex: '1 1 60%', minWidth: 400 }}>
            <Card
              className="hover-card"
              title="识别结果"
              style={{ marginBottom: 16 }}
            >
              <Descriptions column={2} bordered size="small">
                <Descriptions.Item label="服务">
                  <Tag color={typeColors['fingerprint']} style={{ fontSize: 14, padding: '2px 12px' }}>
                    {result.service}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="版本">
                  {result.version || <Text type="secondary">未知</Text>}
                </Descriptions.Item>
                <Descriptions.Item label="操作系统">
                  {result.os || <Text type="secondary">未知</Text>}
                </Descriptions.Item>
                <Descriptions.Item label="端口">
                  {result.port || <Text type="secondary">未知</Text>}
                </Descriptions.Item>
                <Descriptions.Item label="原始 Banner" span={2}>
                  <Text code style={{ wordBreak: 'break-all', fontSize: 12 }}>
                    {result.raw_banner}
                  </Text>
                </Descriptions.Item>
              </Descriptions>

              <div style={{ marginTop: 16 }}>
                <Text type="secondary">置信度</Text>
                <Progress
                  percent={Math.round(result.confidence * 100)}
                  strokeColor={confidenceColor}
                  format={(p) => <span style={{ color: confidenceColor }}>{p}%</span>}
                  style={{ marginTop: 4 }}
                />
              </div>
            </Card>

            <Card className="hover-card" title="指纹 JSON" size="small">
              <JsonHighlight data={{
                service: result.service,
                version: result.version,
                os: result.os,
                port: result.port,
                confidence: result.confidence,
                raw_banner: result.raw_banner,
              }} />
            </Card>
          </div>

          {/* 右侧：关联知识 */}
          <div style={{ flex: '1 1 35%', minWidth: 300 }}>
            <Card
              className="hover-card"
              title={
                <>
                  <DatabaseOutlined style={{ marginRight: 8 }} />
                  关联知识（RAG 检索）
                </>
              }
            >
              {result.matched_knowledge && result.matched_knowledge.length > 0 ? (
                <Timeline
                  items={result.matched_knowledge.map((k, i) => ({
                    dot: typeIcons[k.metadata?.type] || <DatabaseOutlined />,
                    children: (
                      <div key={i} style={{ paddingBottom: 8 }}>
                        <Tag color={typeColors[k.metadata?.type]} style={{ marginBottom: 4 }}>
                          {typeLabels[k.metadata?.type] || k.metadata?.type}
                        </Tag>
                        <div style={{ fontWeight: 600, marginBottom: 4 }}>
                          {k.metadata?.title}
                        </div>
                        <div style={{ color: '#8b949e', fontSize: 13, lineHeight: 1.6 }}>
                          {k.content?.slice(0, 250)}
                          {k.content?.length > 250 ? '...' : ''}
                        </div>
                      </div>
                    ),
                  }))}
                />
              ) : (
                <Empty description="未检索到关联知识" />
              )}
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}

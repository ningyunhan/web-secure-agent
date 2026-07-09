import { useState } from 'react';
import { Button, Table, Card, Spin, Alert, Row, Col, Statistic } from 'antd';
import { PlayCircleOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { Column } from '@ant-design/charts';
import { runBatchTest } from '../api';

interface DetailItem {
  banner: string;
  llm_service: string;
  regex_service: string;
  true_service: string;
  llm_correct: boolean;
  regex_correct: boolean;
}

interface BatchResult {
  total: number;
  llm: { service_accuracy: number; version_accuracy: number };
  regex: { service_accuracy: number; version_accuracy: number };
  details: DetailItem[];
}

export default function BatchTest({ backendOnline }: { backendOnline: boolean }) {
  const [data, setData] = useState<BatchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleRun = async () => {
    setError('');
    setLoading(true);
    setData(null);
    try {
      const res = await runBatchTest();
      setData(res.data);
    } catch (e: any) {
      setError(e.response?.data?.detail || '批量测试失败，请检查后端服务和 API Key 配置');
    }
    setLoading(false);
  };

  const columns = [
    {
      title: '#',
      render: (_: any, __: any, i: number) => i + 1,
      width: 50,
    },
    {
      title: 'Banner',
      dataIndex: 'banner',
      ellipsis: true,
      render: (v: string) => <span style={{ fontFamily: 'monospace', fontSize: 12 }}>{v}</span>,
    },
    { title: 'LLM', dataIndex: 'llm_service', width: 100 },
    { title: '正则', dataIndex: 'regex_service', width: 100 },
    { title: '正确答案', dataIndex: 'true_service', width: 100 },
    {
      title: 'LLM',
      width: 60,
      render: (_: any, r: DetailItem) =>
        r.llm_correct
          ? <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 16 }} />
          : <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 16 }} />,
    },
    {
      title: '正则',
      width: 60,
      render: (_: any, r: DetailItem) =>
        r.regex_correct
          ? <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 16 }} />
          : <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 16 }} />,
    },
  ];

  // 柱状图数据
  const chartData = data
    ? [
        { metric: '服务名准确率', method: 'LLM+RAG', value: Math.round(data.llm.service_accuracy * 100) },
        { metric: '服务名准确率', method: '纯正则', value: Math.round(data.regex.service_accuracy * 100) },
        { metric: '版本号准确率', method: 'LLM+RAG', value: Math.round(data.llm.version_accuracy * 100) },
        { metric: '版本号准确率', method: '纯正则', value: Math.round(data.regex.version_accuracy * 100) },
      ]
    : [];

  const chartConfig = {
    data: chartData,
    xField: 'metric',
    yField: 'value',
    colorField: 'method',
    group: true,
    color: ['#00d4ff', '#ff4d4f'],
    label: {
      text: (d: any) => `${d.value}%`,
      position: 'top' as const,
      style: { fill: '#e6edf3', fontSize: 12 },
    },
    axis: {
      x: { title: false, labelFill: '#8b949e' },
      y: {
        title: '准确率 (%)',
        labelFill: '#8b949e',
        domain: [0, 100] as [number, number],
      },
    },
    legend: {
      color: {
        itemLabelFontSize: 12,
        layout: { justifyContent: 'center' as const },
      },
    },
    style: {
      maxWidth: 40,
      radiusTopLeft: 4,
      radiusTopRight: 4,
    },
    height: 300,
  };

  return (
    <div>
      {!backendOnline && (
        <Alert
          type="error"
          message="后端服务离线"
          description="请先启动后端服务"
          style={{ marginBottom: 16 }}
        />
      )}

      <Card className="hover-card" style={{ marginBottom: 16 }}>
        <Button
          type="primary"
          onClick={handleRun}
          loading={loading}
          size="large"
          icon={<PlayCircleOutlined />}
          disabled={!backendOnline}
        >
          运行批量测试
        </Button>
        <span style={{ marginLeft: 16, color: '#8b949e' }}>
          将对 {data?.total || 20} 条测试数据分别执行 LLM 和正则两种方案
        </span>
      </Card>

      {error && (
        <Alert type="error" message={error} style={{ marginBottom: 16 }} />
      )}

      {loading && (
        <Card style={{ textAlign: 'center', padding: 48 }}>
          <Spin size="large" tip="正在执行批量测试，LLM 调用可能需要 1-2 分钟..." />
        </Card>
      )}

      {data && (
        <>
          {/* 统计卡片 */}
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Card className="hover-card" style={{ borderColor: '#00d4ff40' }}>
                <Statistic
                  title="LLM 服务名准确率"
                  value={(data.llm.service_accuracy * 100).toFixed(0)}
                  suffix="%"
                  valueStyle={{ color: '#00d4ff' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card className="hover-card" style={{ borderColor: '#00d4ff40' }}>
                <Statistic
                  title="LLM 版本号准确率"
                  value={(data.llm.version_accuracy * 100).toFixed(0)}
                  suffix="%"
                  valueStyle={{ color: '#00d4ff' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card className="hover-card" style={{ borderColor: '#ff4d4f40' }}>
                <Statistic
                  title="正则 服务名准确率"
                  value={(data.regex.service_accuracy * 100).toFixed(0)}
                  suffix="%"
                  valueStyle={{ color: '#ff4d4f' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card className="hover-card" style={{ borderColor: '#ff4d4f40' }}>
                <Statistic
                  title="正则 版本号准确率"
                  value={(data.regex.version_accuracy * 100).toFixed(0)}
                  suffix="%"
                  valueStyle={{ color: '#ff4d4f' }}
                />
              </Card>
            </Col>
          </Row>

          {/* 对比柱状图 */}
          <Card className="hover-card" title="准确率对比" style={{ marginBottom: 16 }}>
            <Column {...chartConfig} />
          </Card>

          {/* 逐条对比表 */}
          <Card className="hover-card" title="逐条对比明细">
            <Table
              columns={columns}
              dataSource={data.details}
              rowKey={(_, i) => String(i)}
              pagination={false}
              size="small"
            />
          </Card>
        </>
      )}
    </div>
  );
}

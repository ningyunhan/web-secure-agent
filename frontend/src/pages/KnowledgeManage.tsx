import { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, Select, Tag, message, Popconfirm, Space, Card, Row, Col, Statistic, Progress, Tooltip, Descriptions } from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  BugOutlined,
  SafetyCertificateOutlined,
  DatabaseOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import { listKnowledge, addKnowledge, deleteKnowledge, updateKnowledgeStatus, updateKnowledge } from '../api';

interface KnowledgeItem {
  id: string;
  type: string;
  title: string;
  content: string;
  source: string;
  confidence: number;
  status: string;
  tags: string[];
}

const typeMeta: Record<string, { label: string; color: string; icon: React.ReactNode; borderColor: string }> = {
  fingerprint: {
    label: '指纹特征',
    color: '#00d4ff',
    icon: <DatabaseOutlined style={{ fontSize: 28, color: '#00d4ff' }} />,
    borderColor: '#00d4ff40',
  },
  vulnerability: {
    label: '漏洞情报',
    color: '#ff4d4f',
    icon: <BugOutlined style={{ fontSize: 28, color: '#ff4d4f' }} />,
    borderColor: '#ff4d4f40',
  },
  sop: {
    label: '应急SOP',
    color: '#52c41a',
    icon: <SafetyCertificateOutlined style={{ fontSize: 28, color: '#52c41a' }} />,
    borderColor: '#52c41a40',
  },
};

export default function KnowledgeManage({ backendOnline }: { backendOnline?: boolean }) {
  const [data, setData] = useState<KnowledgeItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [viewModalOpen, setViewModalOpen] = useState(false);
  const [currentItem, setCurrentItem] = useState<KnowledgeItem | null>(null);
  const [editSaving, setEditSaving] = useState(false);
  const [addForm] = Form.useForm();
  const [editForm] = Form.useForm();
  const [filter, setFilter] = useState<string | undefined>(undefined);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await listKnowledge(filter);
      setData(res.data);
    } catch {
      message.error('加载知识列表失败');
    }
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, [filter]);

  const handleAdd = async () => {
    const values = await addForm.validateFields();
    const tags = values.tags
      ? values.tags.split(',').map((t: string) => t.trim()).filter(Boolean)
      : [];
    await addKnowledge({ ...values, tags });
    message.success('添加成功，已立即生效');
    setAddModalOpen(false);
    addForm.resetFields();
    loadData();
  };

  const handleDelete = async (id: string) => {
    await deleteKnowledge(id);
    message.success('删除成功');
    loadData();
  };

  const handleToggleStatus = async (record: KnowledgeItem) => {
    const newStatus = record.status === 'active' ? 'inactive' : 'active';
    await updateKnowledgeStatus(record.id, newStatus);
    message.success(newStatus === 'active' ? '已启用' : '已禁用');
    loadData();
  };

  const openEdit = (record: KnowledgeItem) => {
    setCurrentItem(record);
    editForm.setFieldsValue({
      type: record.type,
      title: record.title,
      content: record.content,
      tags: record.tags?.join(', '),
    });
    setEditModalOpen(true);
  };

  const handleEdit = async () => {
    const values = await editForm.validateFields();
    const tags = values.tags
      ? values.tags.split(',').map((t: string) => t.trim()).filter(Boolean)
      : [];
    setEditSaving(true);
    try {
      await updateKnowledge(currentItem!.id, { ...values, tags });
      message.success('更新成功，已立即生效');
      setEditModalOpen(false);
      loadData();
    } catch {
      message.error('更新失败');
    }
    setEditSaving(false);
  };

  const openView = (record: KnowledgeItem) => {
    setCurrentItem(record);
    setViewModalOpen(true);
  };

  // 统计数据
  const totalCount = data.length;
  const activeCount = data.filter((d) => d.status === 'active').length;
  const typeCounts: Record<string, number> = {
    fingerprint: data.filter((d) => d.type === 'fingerprint').length,
    vulnerability: data.filter((d) => d.type === 'vulnerability').length,
    sop: data.filter((d) => d.type === 'sop').length,
  };

  const columns = [
    {
      title: '状态',
      dataIndex: 'status',
      width: 70,
      render: (status: string) => (
        <Tooltip title={status === 'active' ? '已启用' : '已禁用'}>
          <span
            className={status === 'active' ? 'status-dot status-online' : 'status-dot status-offline'}
            style={{ display: 'inline-block' }}
          />
        </Tooltip>
      ),
    },
    {
      title: '类型',
      dataIndex: 'type',
      width: 120,
      render: (t: string) => {
        const meta = typeMeta[t];
        return meta ? (
          <Tag style={{ color: meta.color, borderColor: meta.color, background: 'transparent' }}>
            {meta.label}
          </Tag>
        ) : (
          <Tag>{t}</Tag>
        );
      },
    },
    { title: '标题', dataIndex: 'title', width: 200 },
    { title: '内容', dataIndex: 'content', ellipsis: true },
    { title: '来源', dataIndex: 'source', width: 80 },
    {
      title: '置信度',
      dataIndex: 'confidence',
      width: 100,
      render: (v: number) => (
        <Progress
          percent={Math.round(v * 100)}
          size="small"
          strokeColor={v >= 0.8 ? '#52c41a' : v >= 0.5 ? '#faad14' : '#ff4d4f'}
        />
      ),
    },
    {
      title: '标签',
      dataIndex: 'tags',
      width: 150,
      render: (tags: string[]) =>
        tags?.map((t) => <Tag key={t} style={{ background: '#21262d', borderColor: '#30363d' }}>{t}</Tag>),
    },
    {
      title: '操作',
      width: 200,
      render: (_: any, r: KnowledgeItem) => (
        <Space>
          <Button
            size="small"
            icon={<EyeOutlined />}
            onClick={() => openView(r)}
          >
            查看
          </Button>
          <Button
            size="small"
            type="primary"
            ghost
            icon={<EditOutlined />}
            onClick={() => openEdit(r)}
          >
            编辑
          </Button>
          <Button
            size="small"
            onClick={() => handleToggleStatus(r)}
            style={r.status === 'active' ? { color: '#faad14' } : { color: '#52c41a' }}
          >
            {r.status === 'active' ? '禁用' : '启用'}
          </Button>
          <Popconfirm
            title="确认删除？此操作不可恢复"
            icon={<ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />}
            onConfirm={() => handleDelete(r.id)}
          >
            <Button danger size="small" icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card className="hover-card" style={{ borderColor: '#58a6ff40' }}>
            <Statistic
              title="知识总量"
              value={totalCount}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#58a6ff' }}
            />
            <div style={{ marginTop: 4, fontSize: 12, color: '#8b949e' }}>
              {activeCount} 条启用 / {totalCount - activeCount} 条禁用
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card className="hover-card" style={{ borderColor: typeMeta.fingerprint.borderColor }}>
            <Statistic
              title="指纹特征"
              value={typeCounts.fingerprint}
              prefix={typeMeta.fingerprint.icon}
              valueStyle={{ color: typeMeta.fingerprint.color }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="hover-card" style={{ borderColor: typeMeta.vulnerability.borderColor }}>
            <Statistic
              title="漏洞情报"
              value={typeCounts.vulnerability}
              prefix={typeMeta.vulnerability.icon}
              valueStyle={{ color: typeMeta.vulnerability.color }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="hover-card" style={{ borderColor: typeMeta.sop.borderColor }}>
            <Statistic
              title="应急SOP"
              value={typeCounts.sop}
              prefix={typeMeta.sop.icon}
              valueStyle={{ color: typeMeta.sop.color }}
            />
          </Card>
        </Col>
      </Row>

      <Card className="hover-card">
        <Space style={{ marginBottom: 16 }}>
          <Select
            placeholder="按类型筛选"
            allowClear
            style={{ width: 200 }}
            onChange={(v) => setFilter(v)}
            options={[
              { value: 'fingerprint', label: '指纹特征' },
              { value: 'vulnerability', label: '漏洞情报' },
              { value: 'sop', label: '应急SOP' },
            ]}
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setAddModalOpen(true)}>
            添加知识
          </Button>
        </Space>

        <Table
          columns={columns}
          dataSource={data}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          size="small"
        />
      </Card>

      {/* 添加知识弹窗 */}
      <Modal
        title="添加知识条目"
        open={addModalOpen}
        onOk={handleAdd}
        onCancel={() => setAddModalOpen(false)}
        width={600}
      >
        <Form form={addForm} layout="vertical">
          <Form.Item name="type" label="类型" rules={[{ required: true }]}>
            <Select
              options={[
                { value: 'fingerprint', label: '指纹特征' },
                { value: 'vulnerability', label: '漏洞情报' },
                { value: 'sop', label: '应急SOP' },
              ]}
            />
          </Form.Item>
          <Form.Item name="title" label="标题" rules={[{ required: true }]}>
            <Input placeholder="如：Nginx Banner 特征" />
          </Form.Item>
          <Form.Item name="content" label="内容" rules={[{ required: true }]}>
            <Input.TextArea rows={4} placeholder="详细描述知识内容" />
          </Form.Item>
          <Form.Item name="tags" label="标签（逗号分隔）">
            <Input placeholder="如：web, http, nginx" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 查看知识弹窗 */}
      <Modal
        title="知识详情"
        open={viewModalOpen}
        onCancel={() => setViewModalOpen(false)}
        footer={[
          <Button key="close" onClick={() => setViewModalOpen(false)}>关闭</Button>,
          <Button
            key="edit"
            type="primary"
            icon={<EditOutlined />}
            onClick={() => {
              setViewModalOpen(false);
              if (currentItem) openEdit(currentItem);
            }}
          >
            编辑
          </Button>,
        ]}
        width={640}
      >
        {currentItem && (
          <Descriptions column={1} bordered size="small" style={{ background: '#0d1117' }}>
            <Descriptions.Item label="类型">
              {(() => {
                const meta = typeMeta[currentItem.type];
                return meta ? (
                  <Tag style={{ color: meta.color, borderColor: meta.color, background: 'transparent' }}>
                    {meta.label}
                  </Tag>
                ) : <Tag>{currentItem.type}</Tag>;
              })()}
            </Descriptions.Item>
            <Descriptions.Item label="标题">{currentItem.title}</Descriptions.Item>
            <Descriptions.Item label="内容">
              <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', maxHeight: 300, overflowY: 'auto' }}>
                {currentItem.content}
              </div>
            </Descriptions.Item>
            <Descriptions.Item label="来源">{currentItem.source}</Descriptions.Item>
            <Descriptions.Item label="置信度">
              <Progress
                percent={Math.round(currentItem.confidence * 100)}
                size="small"
                style={{ width: 200 }}
                strokeColor={currentItem.confidence >= 0.8 ? '#52c41a' : currentItem.confidence >= 0.5 ? '#faad14' : '#ff4d4f'}
              />
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              {currentItem.status === 'active' ? '已启用' : '已禁用'}
            </Descriptions.Item>
            <Descriptions.Item label="标签">
              {currentItem.tags?.length > 0
                ? currentItem.tags.map((t) => <Tag key={t} style={{ background: '#21262d', borderColor: '#30363d' }}>{t}</Tag>)
                : '无'}
            </Descriptions.Item>
            <Descriptions.Item label="ID">
              <span style={{ fontFamily: 'monospace', fontSize: 12, color: '#8b949e' }}>{currentItem.id}</span>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      {/* 编辑知识弹窗 */}
      <Modal
        title="编辑知识条目"
        open={editModalOpen}
        onOk={handleEdit}
        onCancel={() => setEditModalOpen(false)}
        confirmLoading={editSaving}
        width={600}
      >
        <Form form={editForm} layout="vertical">
          <Form.Item name="type" label="类型" rules={[{ required: true }]}>
            <Select
              options={[
                { value: 'fingerprint', label: '指纹特征' },
                { value: 'vulnerability', label: '漏洞情报' },
                { value: 'sop', label: '应急SOP' },
              ]}
            />
          </Form.Item>
          <Form.Item name="title" label="标题" rules={[{ required: true }]}>
            <Input placeholder="如：Nginx Banner 特征" />
          </Form.Item>
          <Form.Item name="content" label="内容" rules={[{ required: true }]}>
            <Input.TextArea rows={6} placeholder="详细描述知识内容" />
          </Form.Item>
          <Form.Item name="tags" label="标签（逗号分隔）">
            <Input placeholder="如：web, http, nginx" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

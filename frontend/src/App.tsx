import { Layout, Menu, theme, Badge, Tooltip } from 'antd';
import { ScanOutlined, BarChartOutlined, DatabaseOutlined } from '@ant-design/icons';
import { useState, useEffect } from 'react';
import axios from 'axios';
import SingleRecognize from './pages/SingleRecognize';
import BatchTest from './pages/BatchTest';
import KnowledgeManage from './pages/KnowledgeManage';

const { Header, Sider, Content } = Layout;

export default function App() {
  const [page, setPage] = useState('single');
  const [collapsed, setCollapsed] = useState(false);
  const [backendOnline, setBackendOnline] = useState(false);
  const {
    token: { colorBgContainer },
  } = theme.useToken();

  // 后端健康检查
  useEffect(() => {
    const checkHealth = async () => {
      try {
        await axios.get('http://localhost:8000/', { timeout: 3000 });
        setBackendOnline(true);
      } catch {
        setBackendOnline(false);
      }
    };
    checkHealth();
    const timer = setInterval(checkHealth, 10000);
    return () => clearInterval(timer);
  }, []);

  const menuItems = [
    { key: 'single', icon: <ScanOutlined />, label: '单条识别' },
    { key: 'batch', icon: <BarChartOutlined />, label: '批量测试' },
    { key: 'knowledge', icon: <DatabaseOutlined />, label: '知识库管理' },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        breakpoint="lg"
        className="sidebar-gradient"
        width={220}
      >
        <div
          className="sidebar-logo"
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
          }}
        >
          <span style={{ fontSize: 24 }}>🔐</span>
          {!collapsed && (
            <span
              style={{
                color: '#00d4ff',
                fontSize: 16,
                fontWeight: 600,
                whiteSpace: 'nowrap',
              }}
            >
              资产指纹识别
            </span>
          )}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[page]}
          items={menuItems}
          onClick={(e) => setPage(e.key)}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: '#161b22',
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid #2a3142',
          }}
        >
          <span style={{ fontSize: 18, fontWeight: 500, color: '#e6edf3' }}>
            网络安全资产指纹识别系统
          </span>
          <Tooltip title={backendOnline ? '后端服务在线' : '后端服务离线'}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ color: '#8b949e', fontSize: 13 }}>
                {backendOnline ? '服务正常' : '服务离线'}
              </span>
              <div
                className={backendOnline ? 'status-dot-online' : 'status-dot-offline'}
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  background: backendOnline ? '#52c41a' : '#ff4d4f',
                }}
              />
            </div>
          </Tooltip>
        </Header>
        <Content
          style={{
            margin: 24,
            padding: 24,
            background: '#161b22',
            borderRadius: 12,
            border: '1px solid #2a3142',
          }}
        >
          <div key={page} className="page-fade-in">
            {page === 'single' && <SingleRecognize backendOnline={backendOnline} />}
            {page === 'batch' && <BatchTest backendOnline={backendOnline} />}
            {page === 'knowledge' && <KnowledgeManage backendOnline={backendOnline} />}
          </div>
        </Content>
      </Layout>
    </Layout>
  );
}

import { Layout, Menu, theme, Tooltip } from 'antd';
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
  const [isMobile, setIsMobile] = useState(false);
  const [backendOnline, setBackendOnline] = useState(false);
  const {
    token: { colorBgContainer },
  } = theme.useToken();

  // 响应式：监听窗口大小
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (mobile) setCollapsed(true);
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

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
        breakpoint="md"
        collapsedWidth={isMobile ? 0 : 80}
        className="sidebar-gradient"
        width={220}
        style={{ position: isMobile ? 'fixed' : 'relative', zIndex: 100, height: '100vh' }}
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
            padding: isMobile ? '0 12px' : '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid #2a3142',
          }}
        >
          <span style={{ fontSize: isMobile ? 14 : 18, fontWeight: 500, color: '#e6edf3', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {isMobile ? '资产指纹识别' : '网络安全资产指纹识别系统'}
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
            margin: isMobile ? 8 : 24,
            padding: isMobile ? 12 : 24,
            background: '#161b22',
            borderRadius: isMobile ? 8 : 12,
            border: '1px solid #2a3142',
            overflowX: 'hidden',
          }}
        >
          <div className="page-fade-in">
            <div style={{ display: page === 'single' ? 'block' : 'none' }}>
              <SingleRecognize backendOnline={backendOnline} />
            </div>
            <div style={{ display: page === 'batch' ? 'block' : 'none' }}>
              <BatchTest backendOnline={backendOnline} />
            </div>
            <div style={{ display: page === 'knowledge' ? 'block' : 'none' }}>
              <KnowledgeManage backendOnline={backendOnline} />
            </div>
          </div>
        </Content>
      </Layout>
    </Layout>
  );
}

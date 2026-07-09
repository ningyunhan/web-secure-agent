import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { ConfigProvider, theme } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import 'antd/dist/reset.css'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: theme.darkAlgorithm,
        token: {
          colorPrimary: '#00d4ff',
          colorBgContainer: '#1a1f2e',
          colorBgBase: '#0d1117',
          borderRadius: 8,
          colorBorder: '#2a3142',
          colorText: '#e6edf3',
          colorTextSecondary: '#8b949e',
          fontSize: 14,
        },
        components: {
          Layout: {
            siderBg: '#0d1117',
            headerBg: '#161b22',
            bodyBg: '#0d1117',
          },
          Menu: {
            darkItemBg: '#0d1117',
            darkSubMenuItemBg: '#0d1117',
            darkItemSelectedBg: '#1a2332',
            darkItemHoverBg: '#1a2332',
          },
          Card: {
            colorBgContainer: '#161b22',
            colorBorderSecondary: '#2a3142',
          },
          Table: {
            colorBgContainer: '#161b22',
            headerBg: '#1a2332',
            rowHoverBg: '#1a2332',
          },
          Modal: {
            contentBg: '#161b22',
            headerBg: '#161b22',
          },
        },
      }}
    >
      <App />
    </ConfigProvider>
  </StrictMode>,
)

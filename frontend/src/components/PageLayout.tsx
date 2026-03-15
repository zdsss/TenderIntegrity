import { Layout, Menu } from 'antd'
import { UploadOutlined, HistoryOutlined } from '@ant-design/icons'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'

const { Sider, Content, Header } = Layout

export default function PageLayout() {
  const navigate = useNavigate()
  const { pathname } = useLocation()

  const selectedKey = pathname.startsWith('/tasks') && !pathname.includes('/report')
    ? '/tasks'
    : '/'

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', padding: '0 24px' }}>
        <span style={{ color: 'white', fontSize: 18, fontWeight: 600 }}>
          TenderIntegrity — 标书雷同检测
        </span>
      </Header>
      <Layout>
        <Sider width={200} style={{ background: '#fff' }}>
          <Menu
            mode="inline"
            selectedKeys={[selectedKey]}
            style={{ height: '100%', borderRight: 0 }}
            items={[
              {
                key: '/',
                icon: <UploadOutlined />,
                label: '上传检测',
                onClick: () => navigate('/'),
              },
              {
                key: '/tasks',
                icon: <HistoryOutlined />,
                label: '历史记录',
                onClick: () => navigate('/tasks'),
              },
            ]}
          />
        </Sider>
        <Content style={{ padding: 24, background: '#f5f5f5', minHeight: 280 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}

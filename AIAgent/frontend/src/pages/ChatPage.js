import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Input,
  Button,
  Avatar,
  Space,
  Tag,
  Spin,
  Typography,
  Divider,
  Layout
} from 'antd';
import {
  SendOutlined,
  RobotOutlined,
  UserOutlined,
  HeartOutlined
} from '@ant-design/icons';
import { useDispatch, useSelector } from 'react-redux';
import { sendMessage, clearMessages } from '../store/chatSlice';
import ProductCard from '../components/ProductCard';

const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;
const { Header, Content } = Layout;

const ChatPage = () => {
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const dispatch = useDispatch();
  const { messages, currentSession } = useSelector(state => state.chat);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return;

    const message = inputValue.trim();
    setInputValue('');
    setIsLoading(true);

    try {
      await dispatch(sendMessage({
        user_id: 'user_001',
        message: message,
        session_id: currentSession
      })).unwrap();
    } catch (error) {
      console.error('发送消息失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const renderMessage = (msg, index) => {
    const isUser = msg.type === 'user';

    return (
      <div
        key={index}
        style={{
          display: 'flex',
          justifyContent: isUser ? 'flex-end' : 'flex-start',
          marginBottom: '16px'
        }}
      >
        <div
          style={{
            maxWidth: '70%',
            display: 'flex',
            flexDirection: isUser ? 'row-reverse' : 'row',
            alignItems: 'flex-start',
            gap: '8px'
          }}
        >
          <Avatar
            icon={isUser ? <UserOutlined /> : <RobotOutlined />}
            style={{
              backgroundColor: isUser ? '#1890ff' : '#ff69b4',
              flexShrink: 0
            }}
          />

          <div
            style={{
              backgroundColor: isUser ? '#1890ff' : '#f6f6f6',
              color: isUser ? '#fff' : '#333',
              padding: '12px 16px',
              borderRadius: '12px',
              borderTopLeftRadius: isUser ? '12px' : '4px',
              borderTopRightRadius: isUser ? '4px' : '12px',
              wordBreak: 'break-word'
            }}
          >
            <div>{msg.content}</div>

            {/* 显示处理信息 */}
            {!isUser && msg.metadata && (
              <div style={{ marginTop: '8px', fontSize: '12px', opacity: 0.8 }}>
                <Space size="small">
                  {msg.metadata.intent && (
                    <Tag size="small" color="blue">
                      {msg.metadata.intent}
                    </Tag>
                  )}
                  {msg.metadata.agent_used && (
                    <Tag size="small" color="green">
                      {msg.metadata.agent_used}
                    </Tag>
                  )}
                  {msg.metadata.confidence && (
                    <Tag size="small" color="orange">
                      置信度: {(msg.metadata.confidence * 100).toFixed(0)}%
                    </Tag>
                  )}
                </Space>
              </div>
            )}

            {/* 显示商品推荐 */}
            {!isUser && msg.products && msg.products.length > 0 && (
              <div style={{ marginTop: '12px' }}>
                <Divider style={{ margin: '8px 0', borderColor: '#d9d9d9' }} />
                <Text strong style={{ fontSize: '12px' }}>商品推荐：</Text>
                <div style={{ marginTop: '8px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  {msg.products.slice(0, 3).map((product, idx) => (
                    <div key={idx} style={{ flex: '1', minWidth: '150px' }}>
                      <ProductCard product={product} size="small" />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 显示处理步骤 */}
            {!isUser && msg.processing_steps && msg.processing_steps.length > 0 && (
              <div style={{ marginTop: '8px' }}>
                <details style={{ fontSize: '11px', opacity: 0.7 }}>
                  <summary style={{ cursor: 'pointer' }}>处理步骤</summary>
                  <ul style={{ margin: '4px 0', paddingLeft: '16px' }}>
                    {msg.processing_steps.map((step, idx) => (
                      <li key={idx}>{step}</li>
                    ))}
                  </ul>
                </details>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  const quickQuestions = [
    '我想给3个月宝宝选奶粉',
    '新生儿洗澡注意事项',
    '6个月宝宝辅食推荐',
    '如何选择纸尿裤',
    '宝宝睡眠问题咨询'
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 页面头部 */}
      <Header style={{
        background: '#fff',
        padding: '0 24px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <Space>
          <HeartOutlined style={{ fontSize: '24px', color: '#ff69b4' }} />
          <Title level={3} style={{ margin: 0, color: '#ff69b4' }}>
            母婴智能客服
          </Title>
          <Text type="secondary">专业 · 贴心 · 可信赖</Text>
        </Space>
        <Button
          size="small"
          onClick={() => dispatch(clearMessages())}
        >
          清空对话
        </Button>
      </Header>

      {/* 主聊天区域 */}
      <Content style={{ padding: '24px', display: 'flex', justifyContent: 'center' }}>
        <div style={{ width: '100%', maxWidth: '800px' }}>
          <Card
            style={{ height: '80vh', display: 'flex', flexDirection: 'column' }}
            bodyStyle={{ flex: 1, display: 'flex', flexDirection: 'column' }}
          >
            {/* 欢迎信息 */}
            {messages.length === 0 && (
              <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <Avatar
                  size={64}
                  icon={<RobotOutlined />}
                  style={{ backgroundColor: '#ff69b4', marginBottom: '16px' }}
                />
                <Title level={4}>您好！我是您的专属母婴顾问</Title>
                <Paragraph type="secondary">
                  我可以为您提供专业的母婴产品推荐、育儿知识解答和个性化建议。
                  请告诉我您的需求，我会竭诚为您服务！
                </Paragraph>

                <div style={{ marginTop: '24px' }}>
                  <Text strong>常见问题：</Text>
                  <div style={{ marginTop: '12px' }}>
                    <Space wrap>
                      {quickQuestions.map((question, index) => (
                        <Button
                          key={index}
                          size="small"
                          type="dashed"
                          onClick={() => setInputValue(question)}
                        >
                          {question}
                        </Button>
                      ))}
                    </Space>
                  </div>
                </div>
              </div>
            )}

            {/* 消息列表 */}
            <div
              style={{
                flex: 1,
                overflowY: 'auto',
                padding: '16px 0',
                maxHeight: '500px'
              }}
            >
              {messages.map((msg, index) => renderMessage(msg, index))}
              {isLoading && (
                <div style={{ textAlign: 'center', padding: '16px' }}>
                  <Spin size="small" />
                  <Text type="secondary" style={{ marginLeft: '8px' }}>
                    AI正在思考中...
                  </Text>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* 输入区域 */}
            <div style={{ borderTop: '1px solid #f0f0f0', paddingTop: '16px' }}>
              <Space.Compact style={{ width: '100%' }}>
                <TextArea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="请输入您的问题..."
                  autoSize={{ minRows: 1, maxRows: 4 }}
                  disabled={isLoading}
                />
                <Button
                  type="primary"
                  icon={<SendOutlined />}
                  onClick={handleSend}
                  loading={isLoading}
                  disabled={!inputValue.trim()}
                  style={{ backgroundColor: '#ff69b4', borderColor: '#ff69b4' }}
                >
                  发送
                </Button>
              </Space.Compact>
            </div>
          </Card>
        </div>
      </Content>
    </Layout>
  );
};

export default ChatPage;
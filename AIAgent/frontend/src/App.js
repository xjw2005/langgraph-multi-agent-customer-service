import React from 'react';
import { Provider } from 'react-redux';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { store } from './store/store';
import ChatPage from './pages/ChatPage';
import './App.css';

function App() {
  return (
    <Provider store={store}>
      <ConfigProvider locale={zhCN}>
        <div className="App">
          <ChatPage />
        </div>
      </ConfigProvider>
    </Provider>
  );
}

export default App;
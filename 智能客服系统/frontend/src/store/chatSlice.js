import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

// 异步thunk - 发送消息
export const sendMessage = createAsyncThunk(
  'chat/sendMessage',
  async (messageData, { rejectWithValue }) => {
    try {
      const response = await axios.post('/api/chat', messageData);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

// 异步thunk - 获取对话历史
export const fetchChatHistory = createAsyncThunk(
  'chat/fetchHistory',
  async (sessionId, { rejectWithValue }) => {
    try {
      const response = await axios.get(`/api/chat/history/${sessionId}`);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

const initialState = {
  messages: [],
  currentSession: null,
  isLoading: false,
  error: null,
  agentStatus: {
    currentAgent: null,
    confidence: 0,
    processingSteps: [],
    isProcessing: false
  }
};

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    clearMessages: (state) => {
      state.messages = [];
      state.currentSession = null;
      state.error = null;
    },
    addUserMessage: (state, action) => {
      state.messages.push({
        type: 'user',
        content: action.payload.message,
        timestamp: new Date().toISOString(),
        id: Date.now()
      });
    },
    addBotMessage: (state, action) => {
      state.messages.push({
        type: 'bot',
        content: action.payload.response,
        timestamp: new Date().toISOString(),
        id: Date.now(),
        metadata: {
          intent: action.payload.intent,
          agent_used: action.payload.agent_used,
          confidence: action.payload.confidence,
          requires_human: action.payload.requires_human
        },
        products: action.payload.products,
        processing_steps: action.payload.processing_steps
      });
    },
    updateAgentStatus: (state, action) => {
      state.agentStatus = { ...state.agentStatus, ...action.payload };
    },
    setCurrentSession: (state, action) => {
      state.currentSession = action.payload;
    }
  },
  extraReducers: (builder) => {
    builder
      // 发送消息
      .addCase(sendMessage.pending, (state, action) => {
        state.isLoading = true;
        state.error = null;

        // 添加用户消息
        state.messages.push({
          type: 'user',
          content: action.meta.arg.message,
          timestamp: new Date().toISOString(),
          id: Date.now()
        });

        // 更新Agent状态
        state.agentStatus.isProcessing = true;
        state.agentStatus.processingSteps = [];
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.isLoading = false;

        // 设置会话ID
        if (action.payload.session_id) {
          state.currentSession = action.payload.session_id;
        }

        // 添加机器人回复
        state.messages.push({
          type: 'bot',
          content: action.payload.response,
          timestamp: new Date().toISOString(),
          id: Date.now(),
          metadata: {
            intent: action.payload.intent,
            agent_used: action.payload.agent_used,
            confidence: action.payload.confidence,
            requires_human: action.payload.requires_human,
            processing_time: action.payload.processing_time
          },
          products: action.payload.products,
          processing_steps: action.payload.processing_steps
        });

        // 更新Agent状态
        state.agentStatus = {
          currentAgent: action.payload.agent_used,
          confidence: action.payload.confidence,
          processingSteps: action.payload.processing_steps,
          isProcessing: false
        };
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
        state.agentStatus.isProcessing = false;

        // 添加错误消息
        state.messages.push({
          type: 'bot',
          content: '抱歉，系统暂时无法处理您的请求，请稍后重试。',
          timestamp: new Date().toISOString(),
          id: Date.now(),
          metadata: {
            error: true
          }
        });
      })

      // 获取历史记录
      .addCase(fetchChatHistory.fulfilled, (state, action) => {
        // 处理历史记录数据
        if (action.payload.summary) {
          // 可以根据需要处理历史数据
        }
      });
  }
});

export const {
  clearMessages,
  addUserMessage,
  addBotMessage,
  updateAgentStatus,
  setCurrentSession
} = chatSlice.actions;

export default chatSlice.reducer;
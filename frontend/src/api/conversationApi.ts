import apiClient from './client';

export interface ConversationMessage {
  id: string;
  sessionId: string;
  role: 'user' | 'assistant';
  content: string;
  intent?: string;
  entities?: Record<string, unknown>;
  response?: string;
  createdAt: string;
}

export interface ConversationRequest {
  message: string;
  sessionId?: string;
}

export interface ConversationResponse {
  sessionId: string;
  message: ConversationMessage;
  suggestedActions?: string[];
}

export const conversationApi = {
  sendMessage: (data: ConversationRequest) => 
    apiClient.post<ConversationResponse>('/conversation/message', data),
  
  getSessionHistory: (sessionId: string) => 
    apiClient.get<ConversationMessage[]>(`/conversation/session/${sessionId}`),
};

export default conversationApi;

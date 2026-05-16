import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
});

export interface Company {
  id: string;
  name: string;
  domain?: string;
  website?: string;
  industry?: string;
  size?: string;
  location?: string;
  description?: string;
  tech_stack?: Record<string, any>;
  hiring_trends?: Record<string, any>;
  summary?: string;
  logo_url?: string;
  linkedin_url?: string;
  research_status: string;
  research_completed_at?: string;
  meta_data?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface CompanySearchResult {
  name: string;
  domain?: string;
  website?: string;
  description?: string;
  industry?: string;
}

export interface Person {
  id: string;
  name: string;
  title?: string;
  role_category?: string;
  linkedin_url?: string;
  recent_posts?: any[];
  activity_summary?: string;
  relevance_score?: number;
  created_at: string;
}

export interface Template {
  id: string;
  company_id: string;
  template_type: string;
  title: string;
  content: string;
  tone?: string;
  target_person_id?: string;
  evaluation_scores?: Record<string, number>;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources_used?: any[];
  evaluation_scores?: Record<string, number>;
  created_at: string;
}

export interface ResearchStatus {
  company_id: string;
  status: string;
  progress?: Record<string, any>;
  completed_steps: string[];
  current_step?: string;
}

export interface AgentRun {
  id: string;
  agent_type: string;
  status: string;
  tokens_used?: number;
  duration_ms?: number;
  started_at?: string;
  completed_at?: string;
}

function normalizeResponse<T>(response: any): { ok: boolean; data: T; error: any } {
  return { ok: true, data: response.data as T, error: null };
}

function handleError(err: any): { ok: false; data: null; error: { message: string; details?: any } } {
  const message = err.response?.data?.detail || err.response?.data?.message || err.message || 'Unknown error';
  return { ok: false, data: null, error: { message, details: err.response?.data } };
}

const api = {
  // Companies
  async searchCompanies(query: string) {
    try {
      const res = await client.post('/companies/search', { query });
      return normalizeResponse<CompanySearchResult[]>(res);
    } catch (e) { return handleError(e); }
  },

  async listCompanies() {
    try {
      const res = await client.get('/companies');
      return normalizeResponse<{ companies: Company[]; total: number }>(res);
    } catch (e) { return handleError(e); }
  },

  async getCompany(id: string) {
    try {
      const res = await client.get(`/companies/${id}`);
      return normalizeResponse<Company>(res);
    } catch (e) { return handleError(e); }
  },

  async createCompany(data: { name: string; domain?: string; website?: string; industry?: string }) {
    try {
      const res = await client.post('/companies', data);
      return normalizeResponse<Company>(res);
    } catch (e) { return handleError(e); }
  },

  async deleteCompany(id: string) {
    try {
      await client.delete(`/companies/${id}`);
      return { ok: true, data: null, error: null };
    } catch (e) { return handleError(e); }
  },

  // Research
  async startResearch(companyId: string) {
    try {
      const res = await client.post(`/companies/${companyId}/research`);
      return normalizeResponse<{ status: string; company_id: string }>(res);
    } catch (e) { return handleError(e); }
  },

  async getResearchStatus(companyId: string) {
    try {
      const res = await client.get(`/companies/${companyId}/research/status`);
      return normalizeResponse<ResearchStatus>(res);
    } catch (e) { return handleError(e); }
  },

  // People
  async getCompanyPeople(companyId: string) {
    try {
      const res = await client.get(`/insights/people/${companyId}`);
      return normalizeResponse<Person[]>(res);
    } catch (e) { return handleError(e); }
  },

  // Templates
  async getTemplates(companyId: string) {
    try {
      const res = await client.get(`/templates/${companyId}`);
      return normalizeResponse<Template[]>(res);
    } catch (e) { return handleError(e); }
  },

  async generateTemplate(data: {
    company_id: string;
    template_type: string;
    target_person_id?: string;
    tone?: string;
    custom_instructions?: string;
  }) {
    try {
      const res = await client.post('/templates/generate', data);
      return normalizeResponse<Template>(res);
    } catch (e) { return handleError(e); }
  },

  // Chat
  async sendMessage(data: { company_id: string; conversation_id?: string; message: string }) {
    try {
      const res = await client.post('/chat', data);
      return normalizeResponse<{ conversation_id: string; message: ChatMessage; related_sources?: any[] }>(res);
    } catch (e) { return handleError(e); }
  },

  async getConversations(companyId: string) {
    try {
      const res = await client.get(`/chat/conversations/${companyId}`);
      return normalizeResponse<{ id: string; title: string; created_at: string }[]>(res);
    } catch (e) { return handleError(e); }
  },

  async getMessages(conversationId: string) {
    try {
      const res = await client.get(`/chat/messages/${conversationId}`);
      return normalizeResponse<ChatMessage[]>(res);
    } catch (e) { return handleError(e); }
  },

  // Insights
  async getAgentRuns(companyId: string) {
    try {
      const res = await client.get(`/insights/agent-runs/${companyId}`);
      return normalizeResponse<AgentRun[]>(res);
    } catch (e) { return handleError(e); }
  },

  async getEvaluations(companyId: string) {
    try {
      const res = await client.get(`/insights/evaluations/${companyId}`);
      return normalizeResponse<any[]>(res);
    } catch (e) { return handleError(e); }
  },

  // Streaming
  createResearchStream(companyId: string): EventSource {
    return new EventSource(`${API_URL}/api/v1/stream/research/${companyId}`);
  },
};

export default api;

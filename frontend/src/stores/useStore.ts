import { create } from 'zustand';
import api, { Company, Person, Template, ChatMessage, ResearchStatus } from '@/services/api';

interface AppState {
  // Companies
  companies: Company[];
  selectedCompany: Company | null;
  loadingCompanies: boolean;

  // Research
  researchStatus: ResearchStatus | null;
  isResearching: boolean;

  // People
  people: Person[];
  loadingPeople: boolean;

  // Templates
  templates: Template[];
  loadingTemplates: boolean;

  // Chat
  messages: ChatMessage[];
  conversationId: string | null;
  loadingChat: boolean;

  // UI
  activeTab: 'overview' | 'people' | 'templates' | 'chat' | 'evaluation';
  error: string | null;

  // Actions
  fetchCompanies: () => Promise<void>;
  selectCompany: (company: Company) => void;
  createCompany: (name: string, domain?: string, website?: string) => Promise<Company | null>;
  deleteCompany: (companyId: string) => Promise<void>;
  startResearch: (companyId: string) => Promise<void>;
  pollResearchStatus: (companyId: string) => Promise<void>;
  fetchPeople: (companyId: string) => Promise<void>;
  fetchTemplates: (companyId: string) => Promise<void>;
  generateTemplate: (data: { company_id: string; template_type: string; tone?: string; custom_instructions?: string; target_person_id?: string }) => Promise<void>;
  sendChatMessage: (companyId: string, message: string) => Promise<void>;
  setActiveTab: (tab: AppState['activeTab']) => void;
  clearError: () => void;
  refreshCompany: (companyId: string) => Promise<void>;
}

export const useStore = create<AppState>((set, get) => ({
  companies: [],
  selectedCompany: null,
  loadingCompanies: false,
  researchStatus: null,
  isResearching: false,
  people: [],
  loadingPeople: false,
  templates: [],
  loadingTemplates: false,
  messages: [],
  conversationId: null,
  loadingChat: false,
  activeTab: 'overview',
  error: null,

  fetchCompanies: async () => {
    set({ loadingCompanies: true });
    const res = await api.listCompanies();
    if (res.ok) {
      set({ companies: res.data!.companies, loadingCompanies: false });
    } else {
      set({ error: res.error?.message, loadingCompanies: false });
    }
  },

  selectCompany: (company) => {
    set({ selectedCompany: company, messages: [], conversationId: null, activeTab: 'overview' });
  },

  createCompany: async (name, domain, website) => {
    const res = await api.createCompany({ name, domain, website });
    if (res.ok) {
      const company = res.data!;
      set((state) => ({ companies: [company, ...state.companies], selectedCompany: company }));
      return company;
    } else {
      set({ error: res.error?.message });
      return null;
    }
  },

  deleteCompany: async (companyId) => {
    const res = await api.deleteCompany(companyId);
    if (res.ok) {
      set((state) => {
        const remaining = state.companies.filter((c) => c.id !== companyId);
        return {
          companies: remaining,
          selectedCompany: state.selectedCompany?.id === companyId ? (remaining.length > 0 ? remaining[0] : null) : state.selectedCompany
        };
      });
    } else {
      set({ error: res.error?.message });
    }
  },

  startResearch: async (companyId) => {
    set({ isResearching: true });
    const res = await api.startResearch(companyId);
    if (res.ok) {
      set({ researchStatus: { company_id: companyId, status: 'in_progress', completed_steps: [], current_step: 'research' } });

      // Connect to SSE stream for live updates
      const stream = api.createResearchStream(companyId);
      stream.addEventListener('progress', (e: any) => {
        const data = JSON.parse(e.data);
        set({ researchStatus: { company_id: companyId, ...data } });
      });
      stream.addEventListener('complete', (e: any) => {
        const data = JSON.parse(e.data);
        set({
          researchStatus: { company_id: companyId, ...data },
          isResearching: false,
        });
        stream.close();
        if (data.status === 'completed') {
          get().refreshCompany(companyId);
          get().fetchPeople(companyId);
        }
      });
      stream.addEventListener('error', () => {
        stream.close();
        // Fallback to polling if SSE fails
        set({ isResearching: true });
      });
    } else {
      set({ error: res.error?.message, isResearching: false });
    }
  },

  pollResearchStatus: async (companyId) => {
    const res = await api.getResearchStatus(companyId);
    if (res.ok) {
      const status = res.data!;
      set({ researchStatus: status });
      if (status.status === 'completed' || status.status === 'failed') {
        set({ isResearching: false });
        if (status.status === 'completed') {
          get().refreshCompany(companyId);
          get().fetchPeople(companyId);
        }
      }
    }
  },

  refreshCompany: async (companyId) => {
    const res = await api.getCompany(companyId);
    if (res.ok) {
      const company = res.data!;
      set((state) => ({
        selectedCompany: company,
        companies: state.companies.map((c) => c.id === company.id ? company : c),
      }));
    }
  },

  fetchPeople: async (companyId) => {
    set({ loadingPeople: true });
    const res = await api.getCompanyPeople(companyId);
    if (res.ok) {
      set({ people: res.data!, loadingPeople: false });
    } else {
      set({ loadingPeople: false });
    }
  },

  fetchTemplates: async (companyId) => {
    set({ loadingTemplates: true });
    const res = await api.getTemplates(companyId);
    if (res.ok) {
      set({ templates: res.data!, loadingTemplates: false });
    } else {
      set({ loadingTemplates: false });
    }
  },

  generateTemplate: async (data) => {
    set({ loadingTemplates: true });
    const res = await api.generateTemplate(data);
    if (res.ok) {
      set((state) => ({ templates: [res.data!, ...state.templates], loadingTemplates: false }));
    } else {
      set({ error: res.error?.message, loadingTemplates: false });
    }
  },

  sendChatMessage: async (companyId, message) => {
    const { conversationId, messages } = get();
    const userMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: message,
      created_at: new Date().toISOString(),
    };
    set({ messages: [...messages, userMsg], loadingChat: true });

    const res = await api.sendMessage({
      company_id: companyId,
      conversation_id: conversationId || undefined,
      message,
    });

    if (res.ok) {
      const data = res.data!;
      set((state) => ({
        messages: [...state.messages.filter(m => m.id !== userMsg.id), { ...userMsg, id: `user-${Date.now()}` }, data.message],
        conversationId: data.conversation_id,
        loadingChat: false,
      }));
    } else {
      set({ error: res.error?.message, loadingChat: false });
    }
  },

  setActiveTab: (tab) => set({ activeTab: tab }),
  clearError: () => set({ error: null }),
}));

import React, { useEffect, useState, useRef } from 'react';
import confetti from 'canvas-confetti';
import { 
  Building2, 
  FileSpreadsheet, 
  Package, 
  ShoppingCart, 
  Coins, 
  MessageSquare, 
  Columns, 
  FileText, 
  History, 
  Sun, 
  Moon,
  Sparkles,
  PlusCircle,
  Activity
} from 'lucide-react';

import { ChatContainer } from './components/chat/ChatContainer';
import { ArtifactWorkspace } from './components/workspace/ArtifactWorkspace';
import { TaskHistorySidebar } from './components/history/TaskHistorySidebar';
import { ExportModal } from './components/export/ExportModal';

import { 
  ChatMessage, 
  TaskItem, 
  TaskResult 
} from './types';
import { 
  fetchHealth, 
  fetchTasks, 
  sendChatMessage 
} from './api/client';

export function App() {
  const [darkMode, setDarkMode] = useState(true);
  const [systemStatus, setSystemStatus] = useState<{
    status: string;
    components: Record<string, string>;
  }>({
    status: 'connecting',
    components: { database: 'checking', goszakup_api: 'live', llm_provider: 'openrouter' },
  });

  // Layout View mode: 'split' | 'chat_only' | 'docs_only'
  const [viewMode, setViewMode] = useState<'split' | 'chat_only' | 'docs_only'>('split');
  const [activeTab, setActiveTab] = useState<'tender' | 'pto' | 'stock' | 'orders' | 'financial'>('tender');

  const [isLoading, setIsLoading] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [currentResult, setCurrentResult] = useState<TaskResult | null>(null);

  // Chat conversation messages
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  // History & Export modals
  const [historyTasks, setHistoryTasks] = useState<TaskItem[]>([]);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isExportOpen, setIsExportOpen] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  // Apply dark mode class to root HTML
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
      document.documentElement.classList.remove('light');
    } else {
      document.documentElement.classList.remove('dark');
      document.documentElement.classList.add('light');
    }
  }, [darkMode]);

  // Load initial health and tasks
  const loadInitialData = async () => {
    setIsLoadingHistory(true);
    try {
      const [health, tasks] = await Promise.all([
        fetchHealth(),
        fetchTasks(20),
      ]);
      setSystemStatus(health);
      setHistoryTasks(tasks);

      // Auto-load latest project state if available
      if (tasks.length > 0 && !currentResult) {
        const latest = tasks[0];
        if (latest.result) {
          setTaskId(latest.task_id);
          setCurrentResult(latest.result);
        }
      }
    } catch (err) {
      console.warn('Initial data load warning:', err);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  // Handle sending a chat message
  const handleSendMessage = async (text: string) => {
    const userMsgId = `usr-${Date.now()}`;
    const userTimestamp = new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });

    const userMessage: ChatMessage = {
      id: userMsgId,
      role: 'user',
      content: text,
      timestamp: userTimestamp,
    };

    // Add user message to state
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Build history for backend LLM
      const historyPayload = messages.slice(-6).map((m) => ({
        role: m.role,
        content: m.content,
        sender: m.sender || (m.role === 'user' ? 'user' : 'coo'),
      }));

      const res = await sendChatMessage({
        message: text,
        history: historyPayload,
        current_state: currentResult || undefined,
      });

      const aiMsgId = `ai-${Date.now()}`;
      const aiTimestamp = new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });

      const aiMessage: ChatMessage = {
        id: aiMsgId,
        role: 'assistant',
        content: res.response,
        sender: (res.sender as any) || 'coo',
        senderTitle: res.sender_title || 'Операционный директор (COO)',
        thought: res.thought,
        timestamp: aiTimestamp,
        state: res.state,
        suggestions: res.suggestions || [],
      };

      setMessages((prev) => [...prev, aiMessage]);

      // If backend returned updated state (e.g. pipeline completed), update active artifact
      if (res.state && res.state.selected_tender) {
        setCurrentResult(res.state);

        // If we are on mobile / chat_only, we can stay or user can switch to docs
        try {
          confetti({
            particleCount: 60,
            spread: 60,
            origin: { y: 0.7 },
          });
        } catch (e) {}

        // Reload tasks list
        fetchTasks(20).then(setHistoryTasks).catch(() => {});
      }

    } catch (err: any) {
      console.error('Chat error:', err);
      const errMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `⚠️ Произошла ошибка при обработке запроса: ${err.message || 'Ошибка соединения с API'}. Проверьте статус бэкенда.`,
        sender: 'coo',
        senderTitle: 'Система Nova',
        timestamp: new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearChat = () => {
    setMessages([]);
  };

  const handleNewProject = () => {
    setMessages([]);
    setCurrentResult(null);
    setTaskId(null);
  };

  const handleSelectHistoryTask = (task: TaskItem) => {
    if (task.result) {
      setTaskId(task.task_id);
      setCurrentResult(task.result);

      // Add a greeting into chat explaining loaded project
      const loadMsg: ChatMessage = {
        id: `hist-${Date.now()}`,
        role: 'assistant',
        content: `📁 **Загружен проект из истории:** «${task.result.task}»\n\nВсе сметные ведомости, складские расчеты и заявки отображены в правой панели документов. Вы можете задать мне любые вопросы по этому объекту!`,
        sender: 'coo',
        senderTitle: 'Операционный директор (COO)',
        timestamp: new Date(task.created_at).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }),
        state: task.result,
        suggestions: [
          '📊 Показать подробный финансовый баланс и маржу',
          '📦 Какие материалы в дефиците?',
          '📑 Показать заявки поставщикам',
        ],
      };
      setMessages([loadMsg]);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-[#0B0F19] text-slate-100 selection:bg-cyan-500 selection:text-white overflow-hidden">
      
      {/* Top Main Navigation Header */}
      <header className="h-14 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl px-4 sm:px-6 flex items-center justify-between flex-shrink-0 z-20">
        
        {/* Left: Brand / Logo */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 text-white font-black text-sm">
            N
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm font-bold text-slate-100 tracking-tight">Nova</h1>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800/60">
                AI Workspace
              </span>
            </div>
          </div>
        </div>

        {/* Center: View Switcher (Desktop) */}
        <div className="hidden md:flex items-center gap-1 p-1 rounded-xl bg-slate-900/90 border border-slate-800 text-xs">
          <button
            onClick={() => setViewMode('chat_only')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition-all ${
              viewMode === 'chat_only'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
            title="Только диалоговый чат"
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Только Чат</span>
          </button>

          <button
            onClick={() => setViewMode('split')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition-all ${
              viewMode === 'split'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
            title="Сплит: Чат + Документы"
          >
            <Columns className="w-3.5 h-3.5" />
            <span>Сплит (Чат + Документы)</span>
          </button>

          <button
            onClick={() => setViewMode('docs_only')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition-all ${
              viewMode === 'docs_only'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
            title="Только панель документов"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Документы</span>
            {currentResult && <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />}
          </button>
        </div>

        {/* Right: Actions (Status, History, New, Theme) */}
        <div className="flex items-center gap-2 sm:gap-3">
          
          {/* Live LLM Provider Status Badge */}
          <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-slate-900 border border-slate-800 text-[11px] text-slate-300">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-slate-400">Модель:</span>
            <span className="font-mono text-cyan-300">
              {systemStatus.components?.llm_provider || 'OpenRouter'}
            </span>
          </div>

          {/* New Project Button */}
          <button
            onClick={handleNewProject}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs font-semibold text-slate-200 transition-colors"
            title="Новый проект / очистить"
          >
            <PlusCircle className="w-3.5 h-3.5 text-cyan-400" />
            <span className="hidden sm:inline">Новый запрос</span>
          </button>

          {/* History Drawer Trigger */}
          <button
            onClick={() => setIsHistoryOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs font-semibold text-slate-200 transition-colors"
            title="История расчетов"
          >
            <History className="w-3.5 h-3.5 text-slate-400" />
            <span className="hidden sm:inline">История</span>
            {historyTasks.length > 0 && (
              <span className="px-1.5 py-0.2 rounded-full bg-cyan-500/20 text-cyan-300 text-[10px] font-mono">
                {historyTasks.length}
              </span>
            )}
          </button>

          {/* Dark/Light toggle */}
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="p-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
            title={darkMode ? 'Светлая тема' : 'Темная тема'}
          >
            {darkMode ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
          </button>
        </div>

      </header>

      {/* Main Split-View Workspace Area */}
      <main className="flex-1 flex overflow-hidden p-3 sm:p-4 gap-3 sm:gap-4">
        
        {/* Left Column: Interactive AI Chat */}
        <div
          className={`h-full transition-all duration-300 ${
            viewMode === 'chat_only'
              ? 'w-full max-w-4xl mx-auto'
              : viewMode === 'docs_only'
              ? 'hidden'
              : 'w-full lg:w-[48%] xl:w-[45%]'
          }`}
        >
          <ChatContainer
            messages={messages}
            isLoading={isLoading}
            onSendMessage={handleSendMessage}
            onClearChat={handleClearChat}
            onOpenTab={(tab) => {
              setActiveTab(tab);
              if (viewMode === 'chat_only') setViewMode('split');
            }}
          />
        </div>

        {/* Right Column: Artifacts & Document Workspace */}
        <div
          className={`h-full transition-all duration-300 ${
            viewMode === 'docs_only'
              ? 'w-full max-w-6xl mx-auto'
              : viewMode === 'chat_only'
              ? 'hidden'
              : 'hidden lg:flex flex-1'
          }`}
        >
          <ArtifactWorkspace
            result={currentResult}
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            onExport={() => setIsExportOpen(true)}
          />
        </div>

      </main>

      {/* History Slide-over Drawer */}
      <TaskHistorySidebar
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        tasks={historyTasks}
        currentTaskId={taskId || undefined}
        isLoading={isLoadingHistory}
        onSelectTask={handleSelectHistoryTask}
        onRefresh={() => {
          setIsLoadingHistory(true);
          fetchTasks(20).then(setHistoryTasks).finally(() => setIsLoadingHistory(false));
        }}
      />

      {/* Export Modal */}
      <ExportModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        result={currentResult}
      />

    </div>
  );
}

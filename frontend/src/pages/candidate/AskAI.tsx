import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Send,
  Sparkles,
  Bot,
  User,
  Trash2,
  Loader2,
  Lightbulb,
  ShieldCheck,
} from 'lucide-react';
import { api } from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../components/ui/Toast';
import type { ChatMessage } from '../../types';

export const AskAI: React.FC = () => {
  const { user } = useAuth();
  const toast = useToast();

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: `Hello ${user?.full_name || 'there'}! I am your CVlect AI Career Copilot. I analyze your extracted resume vectors, identify skill gaps against current market openings, and help refine your profile for target positions. What would you like to explore today?`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      is_llm_generated: true,
    },
  ]);

  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const suggestedPrompts = [
    'Which open jobs have the highest match score with my profile?',
    'What critical skills am I missing for senior developer roles?',
    'How can I improve my resume ATS quality score?',
    'Summarize my top qualifications and core strengths',
  ];

  const handleSendMessage = async (textToSend?: string) => {
    const text = textToSend || input;
    if (!text.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Math.random().toString(36).substring(2, 9),
      role: 'user',
      content: text.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await api.assistant.chat({
        message: text.trim(),
      });

      const aiMessage: ChatMessage = {
        id: Math.random().toString(36).substring(2, 9),
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        sources: response.sources,
        is_llm_generated: response.is_llm_generated,
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (err: any) {
      toast.error('Copilot Error', 'Unable to receive response from AI Assistant.');
      const errorMessage: ChatMessage = {
        id: Math.random().toString(36).substring(2, 9),
        role: 'assistant',
        content: 'I encountered an issue connecting to the inference server. Please verify your connection or try again in a moment.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: 'welcome-cleared',
        role: 'assistant',
        content: `Chat session refreshed. How can I assist your career search or resume optimization?`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        is_llm_generated: true,
      },
    ]);
  };

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-8rem)] flex flex-col glass-panel rounded-3xl border border-white/10 shadow-2xl overflow-hidden">
      {/* Copilot Header */}
      <div className="px-6 py-4 border-b border-white/10 bg-slate-900/40 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-violet-600 to-blue-500 p-0.5 shadow-md">
            <div className="w-full h-full bg-[#0a0e1a] rounded-[10px] flex items-center justify-center">
              <Bot className="w-5 h-5 text-violet-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-white tracking-tight">CVlect Career Copilot</h2>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-violet-500/20 text-violet-300 border border-violet-500/30">
                GPT-4o + Vector Engine
              </span>
            </div>
            <p className="text-xs text-slate-400">Contextual resume analysis & job opportunity advisor</p>
          </div>
        </div>

        <button
          onClick={clearChat}
          className="p-2 text-slate-400 hover:text-white rounded-xl hover:bg-white/5 transition-colors"
          title="Reset conversation"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      {/* Messages Stream */}
      <div className="flex-1 p-6 overflow-y-auto space-y-5">
        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex gap-3 max-w-[85%] ${
                msg.role === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'
              }`}
            >
              {/* Avatar */}
              <div
                className={`w-8 h-8 rounded-xl shrink-0 flex items-center justify-center text-xs font-bold shadow-md ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gradient-to-tr from-violet-600 to-indigo-600 text-white'
                }`}
              >
                {msg.role === 'user' ? <User className="w-4 h-4" /> : <Sparkles className="w-4 h-4" />}
              </div>

              {/* Message Bubble */}
              <div
                className={`p-4 rounded-2xl text-sm leading-relaxed shadow-lg ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-r from-violet-600 to-blue-600 text-white rounded-tr-none'
                    : 'glass-panel border border-white/10 text-slate-200 rounded-tl-none'
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.content}</div>

                {/* Sources pill if provided */}
                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-3 pt-2 border-t border-white/10 flex flex-wrap gap-2 text-[11px] text-slate-400">
                    <span className="font-semibold text-slate-300">Indexed Sources:</span>
                    {msg.sources.map((s, i) => (
                      <span key={i} className="px-2 py-0.5 rounded bg-white/5 text-violet-300 border border-white/5">
                        {s.title || `Vector Source ${i + 1}`}
                      </span>
                    ))}
                  </div>
                )}

                <span className="block text-[10px] text-white/50 text-right mt-1.5 font-mono">
                  {msg.timestamp}
                </span>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Loading Bubble */}
        {isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex gap-3 max-w-[85%] mr-auto"
          >
            <div className="w-8 h-8 rounded-xl bg-violet-600/30 border border-violet-500/30 flex items-center justify-center text-violet-400">
              <Loader2 className="w-4 h-4 animate-spin" />
            </div>
            <div className="p-4 rounded-2xl glass-panel border border-white/10 text-slate-400 text-xs flex items-center gap-2">
              <Sparkles className="w-3.5 h-3.5 text-violet-400 animate-pulse" />
              <span>Analyzing resume vectors and query context...</span>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompts Banner */}
      {messages.length <= 2 && (
        <div className="px-6 py-2 border-t border-white/5 flex flex-wrap gap-2 items-center">
          <span className="text-[11px] font-semibold text-slate-400 flex items-center gap-1">
            <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
            Try asking:
          </span>
          {suggestedPrompts.map((prompt, i) => (
            <button
              key={i}
              onClick={() => handleSendMessage(prompt)}
              className="text-xs px-3 py-1 rounded-full bg-white/5 hover:bg-violet-600/20 hover:text-violet-300 border border-white/5 hover:border-violet-500/30 text-slate-300 transition-colors text-left"
            >
              {prompt}
            </button>
          ))}
        </div>
      )}

      {/* Input Area */}
      <div className="p-4 border-t border-white/10 bg-slate-900/60">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex items-end gap-3"
        >
          <div className="flex-1 relative">
            <textarea
              rows={2}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about your resume, missing skills, or job matches..."
              className="w-full px-4 py-3 rounded-2xl glass-input text-sm text-white placeholder-slate-400 border border-white/10 resize-none focus:ring-1 focus:ring-violet-500"
            />
          </div>

          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="p-3.5 rounded-2xl bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-500 hover:to-blue-500 text-white shadow-lg shadow-violet-600/30 disabled:opacity-40 disabled:cursor-not-allowed transition-all cursor-pointer"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
        <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400 px-1">
          <span>Press Enter to send, Shift+Enter for newline</span>
          <span className="flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
            Private & confidential resume context
          </span>
        </div>
      </div>
    </div>
  );
};

'use client';

import { createContext, useContext, useReducer, ReactNode } from 'react';
import { ChartData } from '@/lib/types';

// Chart Context 状态接口
interface ChartState {
  currentChart: ChartData | null;
  chartHistory: ChartData[];
  isCompiling: boolean;
  compilationError: string | null;
}

// Action 类型定义
type ChartAction =
  | { type: 'UPDATE_CHART'; payload: ChartData }
  | { type: 'ADD_TO_HISTORY'; payload: ChartData }
  | { type: 'SET_COMPILING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'CLEAR_ERROR' };

// Context 接口
interface ChartContextType extends ChartState {
  updateChart: (chartData: ChartData) => void;
  addToHistory: (chartData: ChartData) => void;
  setCompiling: (status: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

// 初始状态
const initialState: ChartState = {
  currentChart: null,
  chartHistory: [],
  isCompiling: false,
  compilationError: null,
};

// Reducer 函数
function chartReducer(state: ChartState, action: ChartAction): ChartState {
  switch (action.type) {
    case 'UPDATE_CHART':
      return {
        ...state,
        currentChart: action.payload,
        isCompiling: false,
        compilationError: null,
      };
    case 'ADD_TO_HISTORY':
      return {
        ...state,
        chartHistory: [...state.chartHistory, action.payload],
      };
    case 'SET_COMPILING':
      return {
        ...state,
        isCompiling: action.payload,
      };
    case 'SET_ERROR':
      return {
        ...state,
        compilationError: action.payload,
        isCompiling: false,
      };
    case 'CLEAR_ERROR':
      return {
        ...state,
        compilationError: null,
      };
    default:
      return state;
  }
}

// Context 创建
const ChartContext = createContext<ChartContextType | undefined>(undefined);

// Provider 组件
export function ChartProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(chartReducer, initialState);

  const updateChart = (chartData: ChartData) => {
    dispatch({ type: 'UPDATE_CHART', payload: chartData });
    dispatch({ type: 'ADD_TO_HISTORY', payload: chartData });
  };

  const addToHistory = (chartData: ChartData) => {
    dispatch({ type: 'ADD_TO_HISTORY', payload: chartData });
  };

  const setCompiling = (status: boolean) => {
    dispatch({ type: 'SET_COMPILING', payload: status });
  };

  const setError = (error: string | null) => {
    dispatch({ type: 'SET_ERROR', payload: error });
  };

  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  const value: ChartContextType = {
    ...state,
    updateChart,
    addToHistory,
    setCompiling,
    setError,
    clearError,
  };

  return (
    <ChartContext.Provider value={value}>
      {children}
    </ChartContext.Provider>
  );
}

// Hook 使用 Context
export function useChart() {
  const context = useContext(ChartContext);
  if (context === undefined) {
    throw new Error('useChart must be used within a ChartProvider');
  }
  return context;
} 
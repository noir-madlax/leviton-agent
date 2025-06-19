// Common chart data types
export interface ChartDataItem {
  [key: string]: string | number | boolean | null | undefined
}

export interface TooltipPayload {
  value: number | string
  name: string
  color: string
  dataKey: string
}

export interface TooltipProps {
  active?: boolean
  payload?: TooltipPayload[]
  label?: string | number
}

export interface ChartClickEvent {
  activeTooltipIndex?: number
  activeLabel?: string | number
  activePayload?: TooltipPayload[]
} 
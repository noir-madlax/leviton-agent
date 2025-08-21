import { useChartsT } from '@/i18n/hooks'
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger } from "@/components/ui/select"

export type MetricType = "revenue" | "volume"

interface MetricTypeSelectorProps {
  onChange: (type: MetricType) => void
  value?: MetricType
}

export function MetricTypeSelector({ onChange, value = "revenue" }: MetricTypeSelectorProps) {
  const chartsT = useChartsT()
  return (
    <div className="flex items-center gap-3 mb-0">
      <span className="text-sm text-gray-600">{chartsT('sortedByRevenueOrVolume')} </span>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger id="metric-type" className="w-40 h-8 text-sm">
          {value === "revenue" ? chartsT('revenue') : chartsT('volume')}
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="revenue" className="text-sm">{chartsT('revenue')}</SelectItem>
          <SelectItem value="volume" className="text-sm">{chartsT('volume')}</SelectItem>
        </SelectContent>
      </Select>
      <div className="text-xs text-gray-600 ml-3">
        <div className="flex items-center space-x-1">
          <span className="font-semibold">{chartsT('revenue')}:</span>
          <span>{chartsT('revenueDefinition')}</span>
        </div>
        <div className="flex items-center space-x-1 mt-1">
          <span className="font-semibold">{chartsT('volume')}:</span>
          <span>{chartsT('volumeDefinition')}</span>
        </div>
      </div>
    </div>
  )
} 
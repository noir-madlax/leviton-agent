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
    <div className="flex items-center space-x-4 mb-0">
      <Label htmlFor="metric-type" className="text-lg font-semibold text-gray-800">
      {chartsT('sortedByRevenueOrVolume')} 
      </Label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger id="metric-type" className="w-[180px] text-base">
          {value === "revenue" ? chartsT('revenue') : chartsT('volume')}
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="revenue" className="text-base">
            <span className="font-semibold">{chartsT('revenue')}</span>
          </SelectItem>
          <SelectItem value="volume" className="text-base">
            <span className="font-semibold">{chartsT('volume')}</span>
          </SelectItem>
        </SelectContent>
      </Select>
      <div className="text-sm text-gray-600 ml-4">
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
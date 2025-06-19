import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger } from "@/components/ui/select"

export type MetricType = "revenue" | "volume"

interface MetricTypeSelectorProps {
  onChange: (type: MetricType) => void
  value?: MetricType
}

export function MetricTypeSelector({ onChange, value = "revenue" }: MetricTypeSelectorProps) {
  return (
    <div className="flex items-center space-x-4 mb-5">
      <Label htmlFor="metric-type" className="text-lg font-semibold text-gray-800">
        Choose to show <span className="font-bold">Revenue</span> or <span className="font-bold">Volume</span>:
      </Label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger id="metric-type" className="w-[180px] text-base">
          {value === "revenue" ? "Revenue" : "Volume"}
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="revenue" className="text-base">
            <span className="font-semibold">Revenue</span>
          </SelectItem>
          <SelectItem value="volume" className="text-base">
            <span className="font-semibold">Volume</span>
          </SelectItem>
        </SelectContent>
      </Select>
      <div className="text-sm text-gray-600 ml-4">
        <div className="flex items-center space-x-1">
          <span className="font-semibold">Revenue:</span>
          <span>Total sales value in dollars</span>
        </div>
        <div className="flex items-center space-x-1 mt-1">
          <span className="font-semibold">Volume:</span>
          <span>Total number of packages sold</span>
        </div>
      </div>
    </div>
  )
} 
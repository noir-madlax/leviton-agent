"use client"

import { useState } from "react"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger } from "@/components/ui/select"
import { useChartsT } from "@/i18n/hooks"

export type PriceType = "sku" | "unit"

interface PriceTypeSelectorProps {
  onChange: (value: PriceType) => void
  defaultValue?: PriceType
}

export function PriceTypeSelector({ onChange, defaultValue = "unit" }: PriceTypeSelectorProps) {
  const chartsT = useChartsT()
  const [value, setValue] = useState<PriceType>(defaultValue)

  const handleValueChange = (newValue: PriceType) => {
    setValue(newValue)
    onChange(newValue)
  }

  return (
    <div className="flex items-center space-x-4 mb-3">
      <Label htmlFor="price-type" className="text-lg font-semibold text-gray-800">
         <span className="font-bold">{chartsT('priceType')}</span> :
      </Label>
      <Select value={value} onValueChange={handleValueChange}>
        <SelectTrigger id="price-type" className="w-[180px] text-base">
          {value === "sku" ? chartsT('fullPackPrice') : chartsT('unitPrice')}
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="sku" className="text-base">
            <span className="font-semibold">{chartsT('fullPackPrice')}</span>
          </SelectItem>
          <SelectItem value="unit" className="text-base">
            <span className="font-semibold">{chartsT('unitPrice')}</span>
          </SelectItem>
        </SelectContent>
      </Select>
    </div>
  )
}

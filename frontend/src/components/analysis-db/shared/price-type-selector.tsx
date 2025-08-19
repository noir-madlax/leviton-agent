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
    <div className="flex items-center gap-3 mb-2">
      <span className="text-sm text-gray-600">{chartsT('priceType')} :</span>
      <Select value={value} onValueChange={handleValueChange}>
        <SelectTrigger id="price-type" className="w-40 h-8 text-sm">
          {value === "sku" ? chartsT('fullPackPrice') : chartsT('unitPrice')}
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="sku" className="text-sm">{chartsT('fullPackPrice')}</SelectItem>
          <SelectItem value="unit" className="text-sm">{chartsT('unitPrice')}</SelectItem>
        </SelectContent>
      </Select>
    </div>
  )
}

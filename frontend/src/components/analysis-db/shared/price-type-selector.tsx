"use client"

import { useState } from "react"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger } from "@/components/ui/select"

export type PriceType = "sku" | "unit"

interface PriceTypeSelectorProps {
  onChange: (value: PriceType) => void
  defaultValue?: PriceType
}

export function PriceTypeSelector({ onChange, defaultValue = "unit" }: PriceTypeSelectorProps) {
  const [value, setValue] = useState<PriceType>(defaultValue)

  const handleValueChange = (newValue: PriceType) => {
    setValue(newValue)
    onChange(newValue)
  }

  return (
    <div className="flex items-center space-x-4 mb-5">
      <Label htmlFor="price-type" className="text-lg font-semibold text-gray-800">
        Choose to show <span className="font-bold">Full Pack Price</span> or <span className="font-bold">Unit Price</span>:
      </Label>
      <Select value={value} onValueChange={handleValueChange}>
        <SelectTrigger id="price-type" className="w-[180px] text-base">
          {value === "sku" ? "Full Pack Price" : "Unit Price"}
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="sku" className="text-base">
            <span className="font-semibold">Full Pack Price</span>
          </SelectItem>
          <SelectItem value="unit" className="text-base">
            <span className="font-semibold">Unit Price</span>
          </SelectItem>
        </SelectContent>
      </Select>
      <div className="text-sm text-gray-600 ml-4">
        <div className="flex items-center space-x-1">
          <span className="font-semibold">Full Pack Price:</span>
          <span>Total price for a full package</span>
        </div>
        <div className="flex items-center space-x-1 mt-1">
          <span className="font-semibold">Unit Price:</span>
          <span>Price per individual unit within a package</span>
        </div>
      </div>
    </div>
  )
}

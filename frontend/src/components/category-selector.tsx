"use client"

import React, { useState, useEffect } from 'react'
import { ChevronRight, ChevronDown, ChevronUp, Loader2, Folder, FolderOpen, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

interface CategoryNode {
  category_id: string
  name: string
  level: number
  parent_id?: string
  has_children: boolean
  children_count: number
  children?: CategoryNode[]
}

interface CategorySelectorProps {
  onCategorySelect: (categoryId: string, categoryName: string, level: number, categoryPath?: string) => void
  selectedCategoryId?: string
  selectedCategoryName?: string
  selectedCategoryPath?: string
}

export function CategorySelector({ 
  onCategorySelect, 
  selectedCategoryId, 
  selectedCategoryName,
  selectedCategoryPath
}: CategorySelectorProps) {
  const [rootCategories, setRootCategories] = useState<CategoryNode[]>([])
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())
  const [loadingNodes, setLoadingNodes] = useState<Set<string>>(new Set())
  const [categoryChildren, setCategoryChildren] = useState<Map<string, CategoryNode[]>>(new Map())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showAllCategories, setShowAllCategories] = useState(false)

  const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

  // Load root categories on mount
  useEffect(() => {
    loadRootCategories()
  }, [])

  const loadRootCategories = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await fetch(`${API_BASE_URL}/api/v1/categories/root`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      if (result.success) {
        setRootCategories(result.categories)
      } else {
        throw new Error(result.message || 'Failed to load categories')
      }
    } catch (error) {
      console.error('Failed to load root categories:', error)
      setError('Failed to load categories')
    } finally {
      setLoading(false)
    }
  }

  const loadCategoryChildren = async (parentId: string) => {
    try {
      setLoadingNodes(prev => new Set(prev).add(parentId))
      
      console.log(`🔄 Loading children for parentId: ${parentId}`);
      const response = await fetch(`${API_BASE_URL}/api/v1/categories/children/${parentId}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      console.log(`📡 API Response for ${parentId}:`, result);
      
      if (result.success && result.children && result.children.length > 0) {
        console.log(`✅ Successfully loaded ${result.children.length} children for ${parentId}`);
        console.log(`📋 Children:`, result.children.map((child: CategoryNode) => child.name));
        
        setCategoryChildren(prev => {
          const newMap = new Map(prev)
          newMap.set(parentId, result.children)
          return newMap
        })
        
        // Auto-expand the node
        setExpandedNodes(prev => new Set(prev).add(parentId))
      } else {
        // Enhanced logging for debugging
        console.log(`⚠️ No children available for ${parentId}`);
        console.log(`🔍 Response details: success=${result.success}, children_count=${result.children?.length || 0}`);
        if (result.message) {
          console.log(`💬 Server message: ${result.message}`);
        }
      }
    } catch (error) {
      console.error(`❌ Failed to load children for ${parentId}:`, error)
    } finally {
      setLoadingNodes(prev => {
        const newSet = new Set(prev)
        newSet.delete(parentId)
        return newSet
      })
    }
  }

  const handleNodeClick = (node: CategoryNode) => {
    if (node.has_children) {
      const isCurrentlyExpanded = expandedNodes.has(node.category_id)
      
      if (isCurrentlyExpanded) {
        // If currently expanded, just collapse it
        console.log(`Collapsing ${node.name}`);
        setExpandedNodes(prev => {
          const newSet = new Set(prev)
          newSet.delete(node.category_id)
          return newSet
        })
      } else {
        // If collapsed, load children from backend (no cache check)
        console.log(`Expanding ${node.name}, loading children from backend...`);
        loadCategoryChildren(node.category_id)
      }
    }
  }

  const handleCategorySelect = async (node: CategoryNode) => {
    try {
      // Get full category path
      const response = await fetch(`${API_BASE_URL}/api/v1/categories/path/${node.category_id}`)
      let categoryPath = node.name // fallback
      
      if (response.ok) {
        const result = await response.json()
        if (result.success && result.path_string) {
          categoryPath = result.path_string
        }
      }
      
      // Call the parent callback with path info
      onCategorySelect(node.category_id, node.name, node.level, categoryPath)
      
      // Always load children if this category has children (no cache check)
      if (node.has_children) {
        loadCategoryChildren(node.category_id)
      }
    } catch (error) {
      console.error('Error getting category path:', error)
      onCategorySelect(node.category_id, node.name, node.level, node.name)
    }
  }

  const renderCategoryNode = (node: CategoryNode, depth: number = 0) => {
    const isExpanded = expandedNodes.has(node.category_id)
    const isLoading = loadingNodes.has(node.category_id)
    const hasChildren = node.has_children || categoryChildren.has(node.category_id)
    const children = categoryChildren.get(node.category_id) || []
    const isSelected = selectedCategoryId === node.category_id

    return (
      <div key={node.category_id} className="w-full">
        <div 
          className={`flex items-center gap-2 p-2 hover:bg-gray-50 cursor-pointer rounded ${
            isSelected ? 'bg-blue-50 border border-blue-200' : ''
          }`}
          style={{ paddingLeft: `${depth * 20 + 8}px` }}
        >
          {/* Expand/Collapse Icon */}
          <div className="w-4 h-4 flex items-center justify-center">
            {isLoading ? (
              <Loader2 className="w-3 h-3 animate-spin text-gray-400" />
            ) : hasChildren ? (
              <button 
                onClick={() => handleNodeClick(node)}
                className="w-4 h-4 flex items-center justify-center hover:bg-gray-200 rounded"
              >
                {isExpanded ? (
                  <ChevronDown className="w-3 h-3 text-gray-600" />
                ) : (
                  <ChevronRight className="w-3 h-3 text-gray-600" />
                )}
              </button>
            ) : (
              <div className="w-3 h-3" />
            )}
          </div>

          {/* Folder Icon */}
          <div className="w-4 h-4">
            {hasChildren ? (
              isExpanded ? (
                <FolderOpen className="w-4 h-4 text-blue-600" />
              ) : (
                <Folder className="w-4 h-4 text-blue-600" />
              )
            ) : (
              <div className="w-1 h-1 bg-gray-400 rounded-full mx-auto" />
            )}
          </div>

          {/* Category Name */}
          <button
            onClick={() => handleCategorySelect(node)}
            className={`flex-1 text-left text-sm hover:text-blue-600 ${
              isSelected ? 'text-blue-600 font-medium' : 'text-gray-700'
            }`}
          >
            <div className="flex items-center justify-between">
              <span>{node.name}</span>
              {isSelected && (
                <Check className="w-4 h-4 text-green-600 ml-2" />
              )}
            </div>
          </button>
        </div>

        {/* Children */}
        {isExpanded && children.length > 0 && (
          <div className="w-full">
            {children.map(child => renderCategoryNode(child, depth + 1))}
          </div>
        )}
      </div>
    )
  }

  const clearSelection = () => {
    onCategorySelect('', '', 0, '')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="w-6 h-6 animate-spin" />
        <span className="ml-2 text-gray-600">Loading categories...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 text-center">
        <p className="text-red-600 mb-4">{error}</p>
        <Button onClick={loadRootCategories} variant="outline" size="sm">
          Retry
        </Button>
      </div>
    )
  }

  return (
    <div className="w-full">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b bg-gray-50">
        <h3 className="font-medium text-gray-900">Select</h3>
        {selectedCategoryId && (
          <Button 
            onClick={clearSelection} 
            variant="outline" 
            size="sm"
            className="text-xs"
          >
            Clear Selection
          </Button>
        )}
      </div>

      {/* Selected Category Display */}
      {selectedCategoryPath && (
        <div className="p-3 bg-blue-50 border-b">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-blue-900">Selected:</span>
            <span className="text-sm text-blue-700">{selectedCategoryPath}</span>
          </div>
        </div>
      )}

      {/* Category Tree */}
      <div className="max-h-96 overflow-y-auto">
        {rootCategories.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            No categories available
          </div>
        ) : (
          <div className="p-2">
            {/* 显示前10个或全部categories */}
            {rootCategories
              .slice(0, showAllCategories ? rootCategories.length : 10)
              .map(category => renderCategoryNode(category))}
            
            {/* 如果有超过10个categories，显示展开/收起按钮 */}
            {rootCategories.length > 10 && (
              <div className="pt-2 border-t mt-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAllCategories(!showAllCategories)}
                  className="w-full text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                >
                  {showAllCategories ? (
                    <>
                      <ChevronUp className="w-4 h-4 mr-1" />
                      Show Less ({rootCategories.length - 10} categories hidden)
                    </>
                  ) : (
                    <>
                      <ChevronDown className="w-4 h-4 mr-1" />
                      Show More ({rootCategories.length - 10} more categories)
                    </>
                  )}
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
} 
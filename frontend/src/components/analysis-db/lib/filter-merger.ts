import { ProjectFilters } from '../types/filters'

/**
 * 筛选器合并器
 * 负责合并project级和chart级的筛选器
 */
export class FilterMerger {
  /**
   * 合并project和chart级筛选器
   * @param projectFilters 项目级筛选器
   * @param chartFilters 图表级筛选器
   * @returns 合并后的筛选器
   */
  mergeFilters(projectFilters: ProjectFilters, chartFilters: ProjectFilters): ProjectFilters {
    return {
      categories: this.mergeArray(projectFilters.categories, chartFilters.categories),
      brands: this.mergeArray(projectFilters.brands, chartFilters.brands),
      segments: this.mergeArray(projectFilters.segments, chartFilters.segments),
      extend_fields: this.mergeExtendFields(projectFilters.extend_fields, chartFilters.extend_fields),
      asins: this.mergeArray(projectFilters.asins || [], chartFilters.asins || [])
    }
  }

  /**
   * 合并数组类型的筛选器，去重
   * @param arr1 第一个数组
   * @param arr2 第二个数组
   * @returns 合并后的数组
   */
  private mergeArray(arr1: string[], arr2: string[]): string[] {
    return [...new Set([...arr1, ...arr2])]
  }

  /**
   * 合并扩展字段筛选器
   * @param obj1 第一个扩展字段对象
   * @param obj2 第二个扩展字段对象
   * @returns 合并后的扩展字段对象
   */
  private mergeExtendFields(obj1: Record<string, any>, obj2: Record<string, any>): Record<string, any> {
    const result = { ...obj1 }
    
    Object.keys(obj2).forEach(key => {
      if (obj2[key] !== undefined && obj2[key] !== null) {
        result[key] = obj2[key]
      }
    })
    
    return result
  }
} 
import { ProjectFilters } from '../types/filters'

/**
 * 筛选器同步器
 * 负责处理project级筛选器到chart级筛选器的同步
 */
export class FilterSynchronizer {
  /**
   * 同步project筛选器到chart筛选器
   * @param currentChartFilters 当前chart筛选器
   * @param oldProjectFilters 旧的project筛选器
   * @param newProjectFilters 新的project筛选器
   * @returns 同步后的chart筛选器
   */
  syncProjectToChart(
    currentChartFilters: ProjectFilters,
    oldProjectFilters: ProjectFilters,
    newProjectFilters: ProjectFilters
  ): ProjectFilters {
    const result = { ...currentChartFilters }

    // 处理数组类型的筛选器
    this.syncArrayField(result, 'categories', oldProjectFilters, newProjectFilters)
    this.syncArrayField(result, 'brands', oldProjectFilters, newProjectFilters)
    this.syncArrayField(result, 'segments', oldProjectFilters, newProjectFilters)
    this.syncArrayField(result, 'asins', oldProjectFilters, newProjectFilters)

    // 处理extend_fields
    this.syncExtendFields(result, oldProjectFilters, newProjectFilters)

    // 处理time_period (如果chart级没有设置或使用project级的值，则更新)
    if (result.time_period === oldProjectFilters.time_period) {
      result.time_period = newProjectFilters.time_period
    }

    return result
  }

  /**
   * 同步数组类型的筛选器字段
   * @param result 结果对象
   * @param field 字段名
   * @param oldProjectFilters 旧的project筛选器
   * @param newProjectFilters 新的project筛选器
   */
  private syncArrayField(
    result: ProjectFilters,
    field: keyof ProjectFilters,
    oldProjectFilters: ProjectFilters,
    newProjectFilters: ProjectFilters
  ) {
    if (Array.isArray(result[field])) {
      const currentArray = result[field] as string[]
      const oldProjectArray = (oldProjectFilters[field] as string[]) || []
      const newProjectArray = (newProjectFilters[field] as string[]) || []

      // 移除不再存在于project中的项
      const filtered = currentArray.filter(item => 
        !oldProjectArray.includes(item) || newProjectArray.includes(item)
      )

      // 添加新的project项
      const added = newProjectArray.filter(item => 
        !oldProjectArray.includes(item) && !filtered.includes(item)
      )

      ;(result[field] as string[]) = [...filtered, ...added]
    }
  }

  /**
   * 同步扩展字段筛选器
   * @param result 结果对象
   * @param oldProjectFilters 旧的project筛选器
   * @param newProjectFilters 新的project筛选器
   */
  private syncExtendFields(
    result: ProjectFilters,
    oldProjectFilters: ProjectFilters,
    newProjectFilters: ProjectFilters
  ) {
    // 移除不再存在于project中的extend_fields
    Object.keys(oldProjectFilters.extend_fields).forEach(key => {
      if (!(key in newProjectFilters.extend_fields)) {
        delete result.extend_fields[key]
      }
    })

    // 添加或更新新的extend_fields
    Object.keys(newProjectFilters.extend_fields).forEach(key => {
      result.extend_fields[key] = newProjectFilters.extend_fields[key]
    })
  }
} 
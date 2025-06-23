# Project-Segmentation Integration Design

## Overview

This document describes the integration between the Projects module (`backend/projects`) and the Product Segment module (`backend/product_segment`) for handling the complete project creation workflow.

## Current State Analysis

### Current Synchronous Flow (Step 2 - Generate Project)

```
User clicks "Generate Project" 
    ↓
POST /projects/create
    ↓
ProjectService.create_project()
    ├── 1. Extract ASINs from filters
    ├── 2. Calculate project statistics  
    ├── 3. Create project record
    ├── 4. Save to database
    └── 5. Return response (synchronous)
```

### Problems with Current Approach

1. **Synchronous Blocking**: User waits for all processing to complete
2. **No Progress Feedback**: No way to show progress during long-running operations
3. **Timeout Risk**: Multi-minute processing may cause HTTP timeouts
4. **Monolithic**: All logic in one service method

## Proposed Asynchronous Architecture

### New Flow Design：关键步骤： 5. **Trigger background processing**

```
User clicks "Generate Project"
    ↓
POST /projects/create (Quick Response)
    ├── 1. Extract ASINs from filters
    ├── 2. Calculate basic project statistics
    ├── 3. Create project record (status: "initializing")
    ├── 4. Save to database
    ├── 5. **Trigger background processing**
    └── 6. Return immediate response with project_id
        ↓
Background Task Chain:
    ├── 7. Update status to "processing"
    ├── 8. Call product_segment module
    ├── 9. Execute segmentation pipeline
    ├── 10. Update project with segmentation results
    └── 11. Update status to "completed"
```

### Progress Tracking

```
WebSocket/SSE Stream: /projects/{project_id}/progress
    ├── Status updates
    ├── Progress percentage
    └── Error handling
```

## Implementation Plan

### Phase 1: Refactor Current Service

1. Split `create_project` into two methods:

   - `create_project_sync()`: Quick project creation (steps 1-6)
   - `process_project_async()`: Background processing (steps 7-11)
2. Add status tracking:

   - `initializing`: Project created, waiting for processing
   - `processing`: Segmentation in progress
   - `completed`: All processing done
   - `failed`: Processing failed

### Phase 2: Background Task Integration

1. Use FastAPI BackgroundTasks or Celery for async processing
2. Integrate with `product_segment` module
3. Implement progress tracking and updates

### Phase 3: Frontend Integration

1. Modify frontend to handle async responses
2. Add progress bar/status display
3. Implement real-time updates

## Database Schema Changes

### Projects Table Updates

```sql
-- Add status and progress tracking columns
ALTER TABLE projects ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'initializing';
ALTER TABLE projects ADD COLUMN IF NOT EXISTS progress_percent FLOAT DEFAULT 0.0;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS processing_log JSONB;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS segmentation_run_id VARCHAR(50);
ALTER TABLE projects ADD COLUMN IF NOT EXISTS error_message TEXT;
```

### Status Values

- `initializing`: Project created, basic data extracted
- `processing`: Segmentation pipeline running
- `completed`: All processing completed successfully
- `failed`: Processing failed with error

## API Changes

### Current API

```http
POST /projects/create
{
  "project_name": "My Project",
  "filters": {...}
}
Response: 200 OK (after full processing)
{
  "id": "proj_123",
  "status": "completed",
  ...
}
```

### New API

```http
POST /projects/create
{
  "project_name": "My Project", 
  "filters": {...}
}
Response: 202 Accepted (immediate)
{
  "id": "proj_123",
  "status": "initializing",
  "progress_url": "/projects/proj_123/progress"
}

GET /projects/proj_123/progress
Response: 200 OK
{
  "status": "processing",
  "progress_percent": 45.5,
  "current_stage": "segmentation",
  "estimated_completion": "2024-01-15T10:30:00Z"
}
```

## Integration with Product Segment Module

### Service Layer Integration

```python
class ProjectService:
    def __init__(self):
        self.supabase = get_supabase_client()
        self.segmentation_service = DatabaseProductSegmentationService()
  
    async def process_project_async(self, project_id: str):
        """Background processing pipeline"""
        try:
            # Update status to processing
            await self._update_project_status(project_id, "processing", 0)
          
            # Get project data
            project = await self.get_project(project_id)
          
            # Call product segmentation
            segmentation_request = StartSegmentationRequest(
                product_ids=project.selected_product_asins,
                product_category=project.selected_categories[0]  # Primary category
            )
          
            # Start segmentation run
            run_id = await self.segmentation_service.create_run(segmentation_request)
          
            # Update project with segmentation run ID
            await self._update_project_segmentation_run(project_id, run_id)
          
            # Execute segmentation (this takes time)
            await self.segmentation_service.execute_run(run_id)
          
            # Update project status
            await self._update_project_status(project_id, "completed", 100)
          
        except Exception as e:
            await self._update_project_status(project_id, "failed", 0, str(e))
            raise
```

### Progress Tracking Integration

```python
async def get_project_progress(self, project_id: str) -> Dict:
    """Get current project processing progress"""
    project = await self.get_project(project_id)
  
    if project.status == "processing" and project.segmentation_run_id:
        # Get progress from segmentation service
        seg_progress = await self.segmentation_service.get_run_progress(
            project.segmentation_run_id
        )
        return {
            "status": project.status,
            "progress_percent": seg_progress.progress_percent,
            "current_stage": seg_progress.stage,
            "estimated_completion": seg_progress.estimated_completion
        }
  
    return {
        "status": project.status,
        "progress_percent": project.progress_percent,
        "current_stage": project.status
    }
```

## Error Handling

### Failure Scenarios

1. **ASIN Extraction Failure**: Return error immediately
2. **Segmentation Service Unavailable**: Mark project as failed
3. **Processing Timeout**: Implement retry logic
4. **Database Connection Issues**: Rollback and retry

### Recovery Mechanisms

1. **Retry Logic**: Automatic retry for transient failures
2. **Manual Restart**: Admin can restart failed projects
3. **Partial Results**: Save intermediate results for debugging

## Testing Strategy

### Unit Tests

- Test synchronous project creation
- Test async processing pipeline
- Test error handling scenarios

### Integration Tests

- Test full workflow end-to-end
- Test progress tracking
- Test failure scenarios

### Load Testing

- Test with multiple concurrent project creations
- Test system behavior under load

## Deployment Considerations

### Environment Variables

```env
# Background task processing
ENABLE_ASYNC_PROCESSING=true
MAX_CONCURRENT_PROJECTS=5

# Progress tracking
PROGRESS_UPDATE_INTERVAL=30  # seconds
```

### Monitoring

- Track processing times
- Monitor failure rates
- Alert on stuck projects

## Timeline

### Week 1: Core Refactoring

- Implement async project creation
- Add status tracking
- Basic progress API

### Week 2: Segmentation Integration

- Integrate with product_segment module
- Implement background processing
- Error handling

### Week 3: Frontend Integration

- Update frontend for async flow
- Add progress display
- Testing and debugging

### Week 4: Production Deployment

- Load testing
- Documentation
- Deployment and monitoring

## Conclusion

This design provides:

1. **Better User Experience**: Immediate feedback with progress tracking
2. **Scalable Architecture**: Async processing prevents blocking
3. **Maintainable Code**: Clear separation of concerns
4. **Robust Error Handling**: Comprehensive failure management
5. **Production Ready**: Monitoring and deployment considerations

The integration leverages the existing `product_segment` module's proven async architecture while maintaining compatibility with the current projects workflow.

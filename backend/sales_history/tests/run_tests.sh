#!/bin/bash
"""
Sales History API Test Runner

This script runs the sales history API tests and provides cleanup options.

Usage:
    ./run_tests.sh [options]

Options:
    --test-only      Run tests only (no cleanup)
    --cleanup-only   Run cleanup only (no tests)
    --dry-run        Show what would be cleaned up without deleting
    --summary        Show current data summary
    --help           Show this help message

Examples:
    ./run_tests.sh                    # Run tests and cleanup
    ./run_tests.sh --test-only        # Run tests only
    ./run_tests.sh --cleanup-only     # Run cleanup only
    ./run_tests.sh --dry-run          # Run tests and show cleanup preview
    ./run_tests.sh --summary          # Show current data summary
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show help
show_help() {
    echo "Sales History API Test Runner"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --test-only      Run tests only (no cleanup)"
    echo "  --cleanup-only   Run cleanup only (no tests)"
    echo "  --dry-run        Show what would be cleaned up without deleting"
    echo "  --summary        Show current data summary"
    echo "  --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run tests and cleanup"
    echo "  $0 --test-only        # Run tests only"
    echo "  $0 --cleanup-only     # Run cleanup only"
    echo "  $0 --dry-run          # Run tests and show cleanup preview"
    echo "  $0 --summary          # Show current data summary"
}

# Function to check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed or not in PATH"
        exit 1
    fi
    
    # Check if required files exist
    if [[ ! -f "$SCRIPT_DIR/test_sales_history_api.py" ]]; then
        print_error "Test file not found: $SCRIPT_DIR/test_sales_history_api.py"
        exit 1
    fi
    
    if [[ ! -f "$SCRIPT_DIR/clear_test_data.py" ]]; then
        print_error "Cleanup file not found: $SCRIPT_DIR/clear_test_data.py"
        exit 1
    fi
    
    # Check if .env file exists
    if [[ ! -f "$BACKEND_DIR/.env" ]]; then
        print_warning ".env file not found in $BACKEND_DIR"
        print_warning "Make sure environment variables are set"
    fi
    
    print_success "Prerequisites check completed"
}

# Function to run tests
run_tests() {
    print_info "Starting sales history API tests..."
    print_info "Test file: $SCRIPT_DIR/test_sales_history_api.py"
    
    cd "$BACKEND_DIR"
    
    # Run the test script
    if python3 "$SCRIPT_DIR/test_sales_history_api.py"; then
        print_success "Tests completed successfully"
        return 0
    else
        print_error "Tests failed"
        return 1
    fi
}

# Function to run cleanup
run_cleanup() {
    local dry_run_flag=""
    if [[ "$1" == "dry-run" ]]; then
        dry_run_flag="--dry-run"
        print_info "Running cleanup in dry-run mode..."
    else
        print_info "Running cleanup..."
    fi
    
    cd "$BACKEND_DIR"
    
    # Run the cleanup script
    if python3 "$SCRIPT_DIR/clear_test_data.py" $dry_run_flag; then
        if [[ "$1" == "dry-run" ]]; then
            print_success "Cleanup preview completed"
        else
            print_success "Cleanup completed successfully"
        fi
        return 0
    else
        print_error "Cleanup failed"
        return 1
    fi
}

# Function to show data summary
show_summary() {
    print_info "Showing current data summary..."
    
    cd "$BACKEND_DIR"
    
    if python3 "$SCRIPT_DIR/clear_test_data.py" --summary; then
        print_success "Data summary completed"
        return 0
    else
        print_error "Data summary failed"
        return 1
    fi
}

# Main execution
main() {
    print_info "Sales History API Test Runner"
    print_info "Script directory: $SCRIPT_DIR"
    print_info "Backend directory: $BACKEND_DIR"
    
    # Parse command line arguments
    TEST_ONLY=false
    CLEANUP_ONLY=false
    DRY_RUN=false
    SHOW_SUMMARY=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --test-only)
                TEST_ONLY=true
                shift
                ;;
            --cleanup-only)
                CLEANUP_ONLY=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --summary)
                SHOW_SUMMARY=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Check prerequisites
    check_prerequisites
    
    # Execute based on options
    if [[ "$SHOW_SUMMARY" == true ]]; then
        show_summary
        exit $?
    fi
    
    if [[ "$CLEANUP_ONLY" == true ]]; then
        if [[ "$DRY_RUN" == true ]]; then
            run_cleanup "dry-run"
        else
            run_cleanup
        fi
        exit $?
    fi
    
    if [[ "$TEST_ONLY" == true ]]; then
        run_tests
        exit $?
    fi
    
    # Default: run tests and cleanup
    print_info "Running full test suite with cleanup..."
    
    # Run tests
    if run_tests; then
        print_success "Tests passed"
        
        # Ask user if they want to clean up
        echo ""
        read -p "Do you want to clean up test data? (y/n): " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if [[ "$DRY_RUN" == true ]]; then
                run_cleanup "dry-run"
            else
                run_cleanup
            fi
        else
            print_info "Skipping cleanup"
        fi
    else
        print_error "Tests failed - skipping cleanup"
        exit 1
    fi
}

# Run main function
main "$@" 
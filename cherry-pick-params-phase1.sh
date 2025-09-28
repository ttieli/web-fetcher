#!/bin/bash
# Cherry-pick Sequence Script for Parameter System (Phase 1)
# Task 1.1: Feature分支分析，为参数系统cherry-pick做准备
# 
# This script cherry-picks the -u/-s/-m parameter system from feature/config-driven-phase1
# to main branch in a safe, incremental manner.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Function to validate git state
validate_git_state() {
    log_info "Validating git state..."
    
    # Check we're in the right repository
    if [[ ! -d ".git" ]]; then
        log_error "Not in a git repository"
        exit 1
    fi
    
    # Check we have clean working directory
    if [[ -n $(git status --porcelain) ]]; then
        log_warning "Working directory is not clean:"
        git status --short
        echo
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Check we're on test branch
    current_branch=$(git rev-parse --abbrev-ref HEAD)
    if [[ "$current_branch" != "test-phase1-params" ]]; then
        log_error "Expected to be on 'test-phase1-params' branch, currently on '$current_branch'"
        exit 1
    fi
    
    # Check feature branch exists
    if ! git rev-parse --verify feature/config-driven-phase1 >/dev/null 2>&1; then
        log_error "Feature branch 'feature/config-driven-phase1' does not exist"
        exit 1
    fi
    
    log_success "Git state validation passed"
}

# Function to create backup before cherry-pick
create_backup() {
    local backup_name="backup-before-params-$(date +%Y%m%d-%H%M%S)"
    log_info "Creating backup branch: $backup_name"
    git branch "$backup_name"
    log_success "Backup created: $backup_name"
}

# Function to test webfetcher.py functionality
test_webfetcher_basic() {
    log_info "Testing basic webfetcher functionality..."
    
    # Test import
    if ! python3 -c "import webfetcher" 2>/dev/null; then
        log_error "webfetcher.py has import errors"
        return 1
    fi
    
    # Test help output (should not crash)
    if ! python3 webfetcher.py --help >/dev/null 2>&1; then
        log_error "webfetcher.py --help failed"
        return 1
    fi
    
    log_success "Basic functionality test passed"
    return 0
}

# Function to cherry-pick a commit with validation
cherry_pick_with_validation() {
    local commit_hash="$1"
    local description="$2"
    local test_function="$3"
    
    log_info "Cherry-picking: $commit_hash - $description"
    
    # Attempt the cherry-pick
    if git cherry-pick "$commit_hash"; then
        log_success "Cherry-pick successful: $commit_hash"
        
        # Run validation test if provided
        if [[ -n "$test_function" ]] && command -v "$test_function" >/dev/null; then
            if $test_function; then
                log_success "Validation passed for $commit_hash"
            else
                log_error "Validation failed for $commit_hash"
                return 1
            fi
        fi
        
        return 0
    else
        log_error "Cherry-pick failed for $commit_hash"
        log_warning "Manual conflict resolution required"
        return 1
    fi
}

# Function to test method parameter functionality
test_method_params() {
    log_info "Testing method parameter functionality..."
    
    # Test --method parameter exists
    if python3 webfetcher.py --help 2>/dev/null | grep -q "\-\-method"; then
        log_success "Method parameter detected"
    else
        log_error "Method parameter not found"
        return 1
    fi
    
    # Test -m shortcut exists
    if python3 webfetcher.py --help 2>/dev/null | grep -q "\-m"; then
        log_success "-m shortcut detected"
    else
        log_error "-m shortcut not found"
        return 1
    fi
    
    return 0
}

# Function to test shortcut parameters
test_shortcut_params() {
    log_info "Testing shortcut parameter functionality..."
    
    # Test -s parameter exists
    if python3 webfetcher.py --help 2>/dev/null | grep -q "\-s.*selenium"; then
        log_success "-s parameter detected"
    else
        log_error "-s parameter not found"
        return 1
    fi
    
    # Test -u parameter exists
    if python3 webfetcher.py --help 2>/dev/null | grep -q "\-u.*urllib"; then
        log_success "-u parameter detected"
    else
        log_error "-u parameter not found"
        return 1
    fi
    
    return 0
}

# Main cherry-pick sequence
main() {
    log_info "Starting Parameter System Cherry-pick (Phase 1)"
    echo "========================================================"
    
    # Step 1: Validate environment
    validate_git_state
    
    # Step 2: Create backup
    create_backup
    
    # Step 3: Initial functionality test
    if ! test_webfetcher_basic; then
        log_error "Initial webfetcher.py test failed - aborting"
        exit 1
    fi
    
    # Step 4: Cherry-pick sequence based on dependency analysis
    log_info "Starting cherry-pick sequence..."
    echo
    
    # Commit 1: Method parameter foundation (159845d)
    if ! cherry_pick_with_validation "159845d" "Add --method/-m parameter and foundation" "test_method_params"; then
        log_error "Failed to cherry-pick method parameter foundation"
        echo "Manual resolution required for commit 159845d"
        echo "After resolving conflicts, run: git cherry-pick --continue"
        exit 1
    fi
    
    # Commit 2: Shortcut parameters (-s/-u) (9cc71b2)  
    if ! cherry_pick_with_validation "9cc71b2" "Add -s/-u shortcut parameters" "test_shortcut_params"; then
        log_error "Failed to cherry-pick shortcut parameters"
        echo "Manual resolution required for commit 9cc71b2"
        echo "After resolving conflicts, run: git cherry-pick --continue"
        exit 1
    fi
    
    # Commit 3: Bug fix for selenium mode (b6fedc7)
    if ! cherry_pick_with_validation "b6fedc7" "Fix selenium priority override bug" "test_webfetcher_basic"; then
        log_error "Failed to cherry-pick selenium bug fix"
        echo "Manual resolution required for commit b6fedc7"
        echo "After resolving conflicts, run: git cherry-pick --continue"
        exit 1
    fi
    
    # Step 5: Final validation
    log_info "Running final validation suite..."
    if test_webfetcher_basic && test_method_params && test_shortcut_params; then
        log_success "All tests passed!"
    else
        log_error "Final validation failed"
        exit 1
    fi
    
    # Step 6: Summary
    echo
    log_success "Cherry-pick sequence completed successfully!"
    echo "========================================================"
    echo "Parameter System Summary:"
    echo "• --method/-m: Choose urllib/selenium/auto"
    echo "• -s/--selenium: Shortcut for selenium mode"
    echo "• -u/--urllib: Shortcut for urllib mode"
    echo "• Includes conflict resolution and validation logic"
    echo
    echo "Next steps:"
    echo "1. Test the parameters with real URLs"
    echo "2. Verify plugin system integration"
    echo "3. Run full test suite if available"
    echo "4. Consider merging to main branch"
    echo
    log_info "Cherry-pick process complete."
}

# Handle script arguments
case "${1:-main}" in
    "main")
        main
        ;;
    "test-basic")
        test_webfetcher_basic
        ;;
    "test-method")
        test_method_params
        ;;
    "test-shortcuts")
        test_shortcut_params
        ;;
    "validate")
        validate_git_state
        ;;
    *)
        echo "Usage: $0 [main|test-basic|test-method|test-shortcuts|validate]"
        echo "  main: Run full cherry-pick sequence (default)"
        echo "  test-basic: Test basic webfetcher functionality"
        echo "  test-method: Test method parameter functionality"
        echo "  test-shortcuts: Test shortcut parameters"
        echo "  validate: Validate git state"
        exit 1
        ;;
esac
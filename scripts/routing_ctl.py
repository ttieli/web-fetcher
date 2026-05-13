#!/usr/bin/env python3
"""
Routing Configuration Management CLI

Provides commands for validating, testing, and managing routing configuration.

Usage:
    ./scripts/routing_ctl.py lint [config_file]
    ./scripts/routing_ctl.py validate [config_file]
    ./scripts/routing_ctl.py show [config_file]
    ./scripts/routing_ctl.py dry-run <url> [--config config_file]
    ./scripts/routing_ctl.py stats [--config config_file]
    ./scripts/routing_ctl.py reload [--config config_file]
"""

import sys
import argparse
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from routing.config_loader import ConfigLoader, ConfigurationError


def cmd_lint(args):
    """Lint configuration file for syntax and schema errors."""
    print(f"Linting configuration: {args.config or 'default'}")
    print("-" * 60)

    try:
        loader = ConfigLoader(args.config)
        config = loader.load()

        print(f"✓ YAML syntax: OK")
        print(f"✓ Schema validation: OK")
        print(f"✓ Version: {config.get('version')}")
        print(f"✓ Rules count: {len(config.get('rules', []))}")

        # Check for duplicate priorities
        rules = config.get('rules', [])
        priorities = [r['priority'] for r in rules]
        duplicates = [p for p in set(priorities) if priorities.count(p) > 1]

        if duplicates:
            print(f"\n⚠ Warning: Duplicate priorities found: {duplicates}")
            print(f"  Rules with same priority will be evaluated in YAML order")

        print(f"\n✅ Configuration is valid")
        return 0

    except ConfigurationError as e:
        print(f"\n❌ Configuration error:")
        print(f"  {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error:")
        print(f"  {e}")
        return 2


def cmd_validate(args):
    """Validate configuration and show detailed information."""
    return cmd_lint(args)


def cmd_show(args):
    """Show configuration details."""
    try:
        loader = ConfigLoader(args.config)
        config = loader.load()

        print(f"Configuration: {loader.config_path}")
        print("=" * 60)

        # Global settings
        print("\nGlobal Settings:")
        for key, value in config.get('global', {}).items():
            print(f"  {key}: {value}")

        # Rules
        print(f"\nRouting Rules ({len(config.get('rules', []))} total):")
        for i, rule in enumerate(config.get('rules', []), 1):
            enabled = "✓" if rule.get('enabled', True) else "✗"
            print(f"\n  {i}. [{enabled}] {rule['name']} (priority: {rule['priority']})")
            print(f"     Fetcher: {rule['action']['fetcher']}")

            # Conditions
            conditions = rule.get('conditions', {})
            if 'domain' in conditions:
                print(f"     Domain: {conditions['domain']}")
            if 'domain_list' in conditions:
                print(f"     Domains: {', '.join(conditions['domain_list'])}")
            if 'url_pattern' in conditions:
                print(f"     Pattern: {conditions['url_pattern']}")
            if 'always' in conditions:
                print(f"     Always: {conditions['always']}")

            # Reason
            if 'reason' in rule['action']:
                print(f"     Reason: {rule['action']['reason']}")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def cmd_dry_run(args):
    """Test routing for a specific URL without actually fetching."""
    from routing.engine import RoutingEngine

    if not args.url:
        print("❌ Error: URL required for dry-run")
        print("Usage: ./scripts/routing_ctl.py dry-run <url>")
        return 1

    try:
        engine = RoutingEngine(args.config)
        decision = engine.evaluate(args.url)

        print(f"Dry-run routing for: {args.url}")
        print("=" * 60)
        print(f"✓ Fetcher: {decision.fetcher}")
        print(f"✓ Rule: {decision.rule_name}")
        print(f"✓ Priority: {decision.priority}")
        print(f"✓ Reason: {decision.reason}")
        print()

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def cmd_reload(args):
    """Reload routing configuration (simulated - actual reload requires running process)."""
    try:
        from routing.engine import RoutingEngine

        print("Reloading routing configuration...")
        print("-" * 60)

        # Create new engine instance (simulates reload)
        engine = RoutingEngine(args.config)
        stats = engine.get_stats()

        print(f"✓ Configuration reloaded successfully")
        print(f"✓ Active rules: {stats['active_rules']}")
        print()
        print("Note: This reloads configuration for testing.")
        print("In production, use application-specific reload mechanism.")
        print()

        return 0

    except Exception as e:
        print(f"❌ Reload failed: {e}")
        return 1


def cmd_stats(args):
    """Show routing engine statistics."""
    try:
        from routing.engine import RoutingEngine

        engine = RoutingEngine(args.config)
        stats = engine.get_stats()

        print("Routing Engine Statistics")
        print("=" * 60)
        print(f"Active rules: {stats['active_rules']}")
        print(f"Total evaluations: {stats['total_evaluations']}")
        print(f"Cache hits: {stats['cache_hits']}")
        print(f"Cache misses: {stats['cache_misses']}")
        print(f"Cache hit rate: {stats['cache_hit_rate']:.2f}%")
        print(f"Last reload: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stats['last_reload']))}")
        print()

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description='Routing Configuration Management CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Lint default configuration
  ./scripts/routing_ctl.py lint

  # Validate specific config file
  ./scripts/routing_ctl.py validate config/routing.yaml

  # Show configuration details
  ./scripts/routing_ctl.py show

  # Test routing for a URL
  ./scripts/routing_ctl.py dry-run https://example.com

  # Show routing statistics
  ./scripts/routing_ctl.py stats

  # Reload configuration
  ./scripts/routing_ctl.py reload
        '''
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # lint command
    lint_parser = subparsers.add_parser('lint', help='Lint configuration file')
    lint_parser.add_argument('config', nargs='?', help='Path to config file (optional)')

    # validate command
    validate_parser = subparsers.add_parser('validate', help='Validate configuration')
    validate_parser.add_argument('config', nargs='?', help='Path to config file (optional)')

    # show command
    show_parser = subparsers.add_parser('show', help='Show configuration details')
    show_parser.add_argument('config', nargs='?', help='Path to config file (optional)')

    # dry-run command
    dry_run_parser = subparsers.add_parser('dry-run', help='Test routing for a URL')
    dry_run_parser.add_argument('url', help='URL to test')
    dry_run_parser.add_argument('--config', nargs='?', help='Path to config file (optional)')

    # reload command
    reload_parser = subparsers.add_parser('reload', help='Reload configuration')
    reload_parser.add_argument('--config', nargs='?', help='Path to config file (optional)')

    # stats command
    stats_parser = subparsers.add_parser('stats', help='Show routing statistics')
    stats_parser.add_argument('--config', nargs='?', help='Path to config file (optional)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute command
    if args.command == 'lint':
        return cmd_lint(args)
    elif args.command == 'validate':
        return cmd_validate(args)
    elif args.command == 'show':
        return cmd_show(args)
    elif args.command == 'dry-run':
        return cmd_dry_run(args)
    elif args.command == 'reload':
        return cmd_reload(args)
    elif args.command == 'stats':
        return cmd_stats(args)

    return 0


if __name__ == '__main__':
    sys.exit(main())

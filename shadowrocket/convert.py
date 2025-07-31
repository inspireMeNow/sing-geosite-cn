#!/usr/bin/env python3

import re
import os
import argparse
from typing import List, Tuple

def classify_domain(domain: str, strategy: str = 'DIRECT') -> str:
    """Return the routing strategy for a domain"""
    return strategy

def convert_regexp_to_domain_set(regexp_pattern: str, strategy: str) -> List[Tuple[str, str]]:
    """Convert regexp patterns to domain rules"""
    rules = []
    pattern = regexp_pattern.replace('regexp:', '')

    if pattern.startswith('(^|\\.)') and pattern.endswith('$'):
        domain_pattern = pattern[6:-1]  # Remove (^|\.) and $

        if '[0-9]' in domain_pattern:
            # Number range patterns, generate DOMAIN-WILDCARD
            base_pattern = re.sub(r'\[[0-9\-]+\]', '*', domain_pattern)
            base_pattern = re.sub(r'\{[0-9,]+\}', '*', base_pattern)
            rules.append((f"DOMAIN-WILDCARD,*.{base_pattern}", classify_domain(base_pattern, strategy)))
        else:
            # Direct domain
            clean_domain = domain_pattern.replace('\\', '')
            rules.append((f"DOMAIN-SUFFIX,{clean_domain}", classify_domain(clean_domain, strategy)))

    return rules

def parse_direct_list(file_path: str, strategy: str = 'DIRECT') -> List[Tuple[str, str]]:
    """Parse domain list file and return rules"""
    rules = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if line.startswith('full:'):
                # Full domain match
                domain = line[5:]
                rules.append((f"DOMAIN,{domain}", classify_domain(domain, strategy)))
            elif line.startswith('regexp:'):
                # Regexp pattern
                regexp_rules = convert_regexp_to_domain_set(line, strategy)
                rules.extend(regexp_rules)
            else:
                # Regular domain
                rules.append((f"DOMAIN-SUFFIX,{line}", classify_domain(line, strategy)))

    return rules

def generate_shadowrocket_module(rules: List[Tuple[str, str]], output_file: str, strategy: str):
    """Generate Shadowrocket Module file"""
    header = f"""#!name=Domain List Module
#!desc=Domain routing rules with {strategy} strategy
#!author=Auto Generated
#!homepage=
#!icon=

[Rule]"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(header + '\n')
        for rule, rule_strategy in rules:
            f.write(f"{rule},{rule_strategy}\n")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Convert domain list to Shadowrocket Module')
    parser.add_argument('-i', '--input', default='direct-list.txt',
                       help='Input file path (default: direct-list.txt)')
    parser.add_argument('-o', '--output', default='direct-list.module',
                       help='Output file path (default: direct-list.module)')
    parser.add_argument('-s', '--strategy', default='DIRECT',
                       choices=['DIRECT', 'PROXY', 'REJECT'],
                       help='Routing strategy (default: DIRECT)')

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file {args.input} not found")
        return

    try:
        print("Parsing domain list...")
        rules = parse_direct_list(args.input, args.strategy)
        print(f"Parsed {len(rules)} rules")

        print("Generating Shadowrocket Module...")
        generate_shadowrocket_module(rules, args.output, args.strategy)
        print(f"Conversion completed! Output: {args.output}")
        print(f"Generated {len(rules)} {args.strategy} rules")

    except Exception as e:
        print(f"Error during conversion: {e}")

if __name__ == '__main__':
    main()

import json
from datetime import datetime
import os

class Week5IssueLogger:
    def __init__(self, log_file="week5_issues_log.json"):
        self.log_file = log_file
        self.issues = self.load_existing()
    
    def load_existing(self):
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r') as f:
                return json.load(f)
        return []
    
    def save(self):
        with open(self.log_file, 'w') as f:
            json.dump(self.issues, f, indent=2)
    
    def log_issue(self, scenario, issue_type, description, severity="medium"):
        entry = {
            "id": len(self.issues) + 1,
            "timestamp": datetime.now().isoformat(),
            "week": 5,
            "scenario": scenario,
            "issue_type": issue_type,
            "description": description,
            "severity": severity,
            "status": "open",
            "resolved_in_version": None
        }
        self.issues.append(entry)
        self.save()
        return entry["id"]
    
    def get_open_issues(self):
        return [i for i in self.issues if i["status"] == "open"]
    
    def get_issues_by_type(self, issue_type):
        return [i for i in self.issues if i["issue_type"] == issue_type]
    
    def mark_resolved(self, issue_id, rubric_version):
        for issue in self.issues:
            if issue["id"] == issue_id:
                issue["status"] = "resolved"
                issue["resolved_in_version"] = rubric_version
                self.save()
                return True
        return False
    
    def generate_summary(self):
        open_issues = self.get_open_issues()
        summary = {
            "total_issues": len(self.issues),
            "open_issues": len(open_issues),
            "resolved_issues": len([i for i in self.issues if i["status"] == "resolved"]),
            "issues_by_type": {},
            "issues_by_severity": {"high": 0, "medium": 0, "low": 0}
        }
        
        for issue in self.issues:
            issue_type = issue["issue_type"]
            summary["issues_by_type"][issue_type] = summary["issues_by_type"].get(issue_type, 0) + 1
            summary["issues_by_severity"][issue["severity"]] += 1
        
        return summary
    
    def export_for_pm(self, output_file="week5_rubric_refinements.md"):
        summary = self.generate_summary()
        
        with open(output_file, 'w') as f:
            f.write(f"# Week 5 Risk Rubric Refinements\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write(f"**Total Issues Logged:** {summary['total_issues']}\n")
            f.write(f"**Open Issues:** {summary['open_issues']}\n\n")
            
            f.write("## Issue Summary\n\n")
            f.write("| Issue Type | Count |\n")
            f.write("|------------|-------|\n")
            for issue_type, count in summary["issues_by_type"].items():
                f.write(f"| {issue_type} | {count} |\n")
            
            f.write("\n## Open Issues Requiring Rubric Changes\n\n")
            for issue in self.get_open_issues():
                f.write(f"### Issue #{issue['id']}: {issue['issue_type']}\n")
                f.write(f"- **Scenario:** {issue['scenario']}\n")
                f.write(f"- **Description:** {issue['description']}\n")
                f.write(f"- **Severity:** {issue['severity']}\n")
                f.write(f"- **Logged:** {issue['timestamp']}\n\n")
            
            f.write("\n## Recommended Rubric Changes\n\n")
            f.write("1. **Adjust magnitude thresholds**\n")
            f.write("   - Current: >10% triggers +20 points\n")
            f.write("   - Recommended: >15% for small datasets\n\n")
            f.write("2. **Add revenue direction weighting**\n")
            f.write("   - Negative revenue should add +25 points regardless of magnitude\n\n")
            f.write("3. **Reduce churn sensitivity**\n")
            f.write("   - Current: >2% churn triggers +25\n")
            f.write("   - Recommended: >3% churn threshold\n\n")
        
        return output_file
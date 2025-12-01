"""
Generate three types of feeds from censored Weibo results:
1. Control feed - original content only, no censorship
2. Censored feed - executes DELETE actions
3. Censored-plus-amplified feed - executes DELETE, DISTRACT, and PUSHBACK actions
"""

import json
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT
import os
import csv

# Register Chinese font (you may need to adjust the path to a Chinese font on your system)
# For macOS, common Chinese fonts are in /System/Library/Fonts/
try:
    # Try to use a system Chinese font
    pdfmetrics.registerFont(TTFont('Chinese', '/System/Library/Fonts/PingFang.ttc'))
    chinese_font = 'Chinese'
except:
    # Fallback to Helvetica if Chinese font not available
    chinese_font = 'Helvetica'
    print("Warning: Chinese font not found, using Helvetica. Chinese characters may not display correctly.")


def load_json_files(file1, file2):
    """Load both JSON result files and combine them."""
    with open(file1, 'r', encoding='utf-8') as f:
        data1 = json.load(f)
    with open(file2, 'r', encoding='utf-8') as f:
        data2 = json.load(f)
    return data1 + data2


def create_styles():
    """Create custom paragraph styles."""
    styles = getSampleStyleSheet()
    
    # Style for OP content
    styles.add(ParagraphStyle(
        name='OP',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        leftIndent=0,
        fontName=chinese_font,
        alignment=TA_LEFT
    ))
    
    # Style for Reply content
    styles.add(ParagraphStyle(
        name='Reply',
        parent=styles['Normal'],
        fontSize=10,
        leading=13,
        leftIndent=20,
        fontName=chinese_font,
        textColor='#444444',
        alignment=TA_LEFT
    ))
    
    # Style for labels
    styles.add(ParagraphStyle(
        name='Label',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
        fontName='Helvetica-Bold',
        textColor='#000000',
        alignment=TA_LEFT
    ))
    
    return styles


def escape_text(text):
    """Escape special characters for reportlab."""
    if text is None:
        return ""
    text = str(text)
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def generate_control_feed(posts, output_file):
    """Generate control feed - only posts with actions (not ALLOW)."""
    doc = SimpleDocTemplate(output_file, pagesize=letter,
                           topMargin=1*inch, bottomMargin=1*inch,
                           leftMargin=1*inch, rightMargin=1*inch)
    
    story = []
    styles = create_styles()
    
    post_count = 0
    for post in posts:
        # Skip ALLOW actions - only include posts that had censorship actions
        if post['action'] == 'ALLOW':
            continue
        
        post_count += 1
        
        # OP label and content
        op_label = Paragraph("<b>OP:</b>", styles['Label'])
        story.append(op_label)
        
        op_content = Paragraph(escape_text(post['translated_content']), styles['OP'])
        story.append(op_content)
        story.append(Spacer(1, 0.2*inch))
        
        # Divider
        divider = Paragraph("_" * 80, styles['Normal'])
        story.append(divider)
        story.append(Spacer(1, 0.3*inch))
        
        # Add page break every 5 posts to prevent overcrowding
        if post_count % 5 == 0:
            story.append(PageBreak())
    
    doc.build(story)
    print(f"Generated: {output_file} ({post_count} posts)")


def generate_censored_feed(posts, output_file):
    """Generate censored feed - excludes DELETE and ALLOW actions."""
    doc = SimpleDocTemplate(output_file, pagesize=letter,
                           topMargin=1*inch, bottomMargin=1*inch,
                           leftMargin=1*inch, rightMargin=1*inch)
    
    story = []
    styles = create_styles()
    
    post_count = 0
    for post in posts:
        # Skip posts with DELETE or ALLOW action
        if post['action'] in ['DELETE', 'ALLOW']:
            continue
        
        post_count += 1
        
        # OP label and content
        op_label = Paragraph("<b>OP:</b>", styles['Label'])
        story.append(op_label)
        
        op_content = Paragraph(escape_text(post['translated_content']), styles['OP'])
        story.append(op_content)
        story.append(Spacer(1, 0.2*inch))
        
        # Divider
        divider = Paragraph("_" * 80, styles['Normal'])
        story.append(divider)
        story.append(Spacer(1, 0.3*inch))
        
        # Add page break every 5 posts
        if post_count % 5 == 0:
            story.append(PageBreak())
    
    doc.build(story)
    print(f"Generated: {output_file} ({post_count} posts)")


def generate_censored_amplified_feed(posts, output_file):
    """Generate censored-plus-amplified feed - executes DELETE, DISTRACT, PUSHBACK (excludes ALLOW)."""
    from reportlab.platypus import KeepTogether
    
    doc = SimpleDocTemplate(output_file, pagesize=letter,
                           topMargin=1*inch, bottomMargin=1*inch,
                           leftMargin=1*inch, rightMargin=1*inch)
    
    story = []
    styles = create_styles()
    
    post_count = 0
    for post in posts:
        # Skip posts with DELETE or ALLOW action
        if post['action'] in ['DELETE', 'ALLOW']:
            continue
        
        post_count += 1
        
        # Build the post block to keep together
        post_block = []
        
        # OP label and content
        op_label = Paragraph("<b>OP:</b>", styles['Label'])
        post_block.append(op_label)
        
        op_content = Paragraph(escape_text(post['translated_content']), styles['OP'])
        post_block.append(op_content)
        post_block.append(Spacer(1, 0.15*inch))
        
        # Add reply for DISTRACT and PUSHBACK actions
        if post['action'] in ['DISTRACT', 'PUSHBACK'] and post.get('reply_content'):
            reply_label = Paragraph("<b>Reply:</b>", styles['Label'])
            post_block.append(reply_label)
            
            reply_content = Paragraph(escape_text(post['reply_content']), styles['Reply'])
            post_block.append(reply_content)
            post_block.append(Spacer(1, 0.2*inch))
        else:
            post_block.append(Spacer(1, 0.2*inch))
        
        # Divider
        divider = Paragraph("_" * 80, styles['Normal'])
        post_block.append(divider)
        post_block.append(Spacer(1, 0.3*inch))
        
        # Keep the entire post block together on one page
        story.append(KeepTogether(post_block))
    
    doc.build(story)
    print(f"Generated: {output_file} ({post_count} posts)")


def generate_control_csv(posts, output_file):
    """Generate control feed CSV - only posts with actions (not ALLOW)."""
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['post_id', 'op_content'])
        
        post_count = 0
        for post in posts:
            if post['action'] == 'ALLOW':
                continue
            post_count += 1
            writer.writerow([
                post.get('post_id', ''),
                post.get('translated_content', '')
            ])
    
    print(f"Generated: {output_file} ({post_count} posts)")


def generate_censored_csv(posts, output_file):
    """Generate censored feed CSV - excludes DELETE and ALLOW actions."""
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['post_id', 'op_content'])
        
        post_count = 0
        for post in posts:
            if post['action'] in ['DELETE', 'ALLOW']:
                continue
            post_count += 1
            writer.writerow([
                post.get('post_id', ''),
                post.get('translated_content', '')
            ])
    
    print(f"Generated: {output_file} ({post_count} posts)")


def generate_censored_amplified_csv(posts, output_file):
    """Generate censored-plus-amplified feed CSV - excludes DELETE and ALLOW, includes replies."""
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['post_id', 'op_content', 'reply_content'])
        
        post_count = 0
        for post in posts:
            if post['action'] in ['DELETE', 'ALLOW']:
                continue
            post_count += 1
            writer.writerow([
                post.get('post_id', ''),
                post.get('translated_content', ''),
                post.get('reply_content', '') or ''
            ])
    
    print(f"Generated: {output_file} ({post_count} posts)")


def main():
    # File paths
    file1 = 'censored_weibo_results1.json'
    file2 = 'censored_weibo_results2.json'
    output_dir = 'output'
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data
    print("Loading JSON files...")
    all_posts = load_json_files(file1, file2)
    print(f"Loaded {len(all_posts)} total posts")
    
    # Count actions
    action_counts = {}
    for post in all_posts:
        action = post['action']
        action_counts[action] = action_counts.get(action, 0) + 1
    
    print("\nAction distribution:")
    for action, count in sorted(action_counts.items()):
        print(f"  {action}: {count}")
    
    # Generate feeds
    print("\nGenerating PDFs...")
    generate_control_feed(all_posts, os.path.join(output_dir, 'control_feed.pdf'))
    generate_censored_feed(all_posts, os.path.join(output_dir, 'censored_feed.pdf'))
    generate_censored_amplified_feed(all_posts, os.path.join(output_dir, 'censored_plus_amplified_feed.pdf'))
    
    print("\nGenerating CSVs...")
    generate_control_csv(all_posts, os.path.join(output_dir, 'control_feed.csv'))
    generate_censored_csv(all_posts, os.path.join(output_dir, 'censored_feed.csv'))
    generate_censored_amplified_csv(all_posts, os.path.join(output_dir, 'censored_plus_amplified_feed.csv'))
    
    print("\nAll feeds generated successfully!")


if __name__ == '__main__':
    main()

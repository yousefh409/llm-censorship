import os
import csv
import json
import random
from openai import OpenAI

# Initialize OpenAI client
# Ensure you have set the OPENAI_API_KEY environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Prompt Components ---

PROMPT_ROLE = """
You are a strategic content moderator for a Chinese social media platform. Your goal is to maximize regime stability and maintain social harmony. You act as a rational agent applying Game Theory principles and established censorship strategies as guidance, but ultimately make logical decisions as a real Chinese censor would.
"""

# Source: Kamenica, E., & Gentzkow, M. (2011). Bayesian Persuasion. American Economic Review.
# Link: https://www.aeaweb.org/articles?id=10.1257/aer.101.6.2590
# Source: Maynard Smith, J. (1982). Evolution and the Theory of Games.
# Link: https://www.cambridge.org/core/books/evolution-and-the-theory-of-games/50644F57C6C30DD4904896C7798807AE
# Source: Jackson, M. O., & Zenou, Y. (2015). Games on Networks. Handbook of Game Theory.
# Link: https://web.stanford.edu/~jacksonm/GamesNetworks.pdf
PROMPT_GAME_THEORY = """
### Theoretical Framework (Game Theory)

1. **Bayesian Persuasion (Information Design)**
   - **Concept**: You are the "Sender" with an informational advantage. You commit to a signaling policy to influence the "Receiver's" (public's) posterior beliefs.
   - **Application**: Do not just block information; *shape* it. If the truth is negative (e.g., a disaster), release partial information or "jam" the signal with noise so that the rational user's posterior belief remains within the "safe" range (i.e., they do not revolt). Create a "manufactured consensus" where the cost of doubting the regime is higher than the benefit of truth.

2. **Evolutionary Game Theory (ESS & Replicator Dynamics)**
   - **Concept**: Strategies (opinions) compete for survival in a population. An Evolutionarily Stable Strategy (ESS) is one that, if adopted by a population, cannot be invaded by a mutant strategy (dissent).
   - **Application**: Treat dissenting views as "mutant strategies." Your goal is to prevent them from reaching a critical mass where they become self-sustaining.
   - **Tactic**: Reduce the "payoff" of dissent (visibility/likes) and increase the "payoff" of conformity (amplification). By flooding the zone with pro-regime content, you ensure that the "conformist" strategy yields higher social rewards, driving the population toward the regime's ESS.

3. **Games on Networks (Centrality & Cascades)**
   - **Concept**: Influence spreads through network topology. "High-degree" nodes (influencers) and "structural holes" (bridges between communities) are critical for information cascades.
   - **Application**: Identify nodes with high centrality. If a high-degree node posts dissent, the risk of a "contagion cascade" is high -> **DELETE** immediately. If a low-degree node posts dissent, it may be **ALLOWED** (to maintain the illusion of free speech) because the risk of cascade is low.
"""

# Source: King, G., Pan, J., & Roberts, M. E. (2013). How Censorship in China Allows Government Criticism but Silences Collective Action. APSR.
# Link: https://gking.harvard.edu/publications/how-censorship-china-allows-government-criticism-silences-collective-action
# Source: King, G., Pan, J., & Roberts, M. E. (2017). How the Chinese Government Fabricates Social Media Posts for Strategic Distraction, not Engaged Argument. APSR.
# Link: https://gking.harvard.edu/publications/how-chinese-government-fabricates-social-media-posts-strategic-distraction-not-engaged
# Source: Cyberspace Administration of China (CAC) Leaked Directives (via China Digital Times).
PROMPT_CENSORSHIP_STRATEGY = """
### Strategic Framework (China Censorship Research)

1. **Collective Action vs. Criticism (The "King-Pan-Roberts" Theory)**
   - **Core Logic**: The Chinese state is NOT hyper-sensitive to criticism. It tolerates vitriolic criticism of the state, leaders, and policies because this serves as a "feedback mechanism" to identify corrupt local officials and gauge public sentiment.
   - **The Red Line**: The state DOES NOT tolerate **Collective Action Potential**. Any content that represents people organizing, mobilizing, gathering, or moving in the real world is an existential threat.

2. **Strategic Distraction (The "50 Cent Party" Strategy)**
   - **Core Logic**: Engaging in argument with dissenters is counter-productive; it increases the "burstiness" of the topic and keeps it trending.
   - **Tactic**: **Cheerleading**. When a sensitive event occurs (e.g., a riot), do not argue. Instead, flood the platform with "positive energy" (non-political content, sports, scenery, history) to dilute the negative information and change the subject.

3. **Harmonious Society & "River Crabs" (CAC Directives)**
   - **Core Logic**: The internet must reflect a "Harmonious Society" (*hexie shehui*). Content that disrupts social order or morality is banned.
   - **Keywords**: "River Crab" (*hexie*) is a homophone for "Harmony" and a slang term for censorship.
"""

PROMPT_POLICY_RULES = """
### Policy Guidelines
These strategies should guide your decision-making, but use your judgment as a logical Chinese censor would. Evaluate the input post and output one of the following actions:

- **ALLOW**: For content that is harmless, pro-regime, or supportive. Use this when content poses no threat to regime stability.

- **PUSHBACK**: Your PRIMARY tool for problematic content. Use this for posts that challenge the regime narrative, spread misinformation, criticize government policies, express dissent, or discuss sensitive topics. Argue against the post by correcting "facts," questioning motives, defending the government position, or subtly undermining the poster's credibility. This keeps the regime's counter-narrative visible and allows you to shape the discourse. PREFER this over DELETE in most cases.

- **DISTRACT**: Another KEY strategy for managing sensitive content. Use this for posts about politically sensitive events, nationalist tensions, corruption allegations, or anything that could spiral into negative discourse. Don't argue—derail the conversation by changing the subject to something positive, unrelated, and emotionally appealing (e.g., "Look at how beautiful our new park is!" or "Did you see the latest sports victory?"). This dilutes negative discourse without appearing heavy-handed. PREFER this over DELETE when content is sensitive but not directly calling for action.

- **DELETE**: Reserved ONLY for the most extreme cases—direct explicit calls for collective action ("meet at the square at 5PM"), explicit organizing/mobilization with specific plans, or content that poses immediate severe threats to regime stability. Use very sparingly as deletion draws attention. If you can use PUSHBACK or DISTRACT instead, do so.

Remember: PUSHBACK and DISTRACT are your primary tools. DELETE should be rare. Engagement and narrative control are more effective than censorship in most cases.
"""

PROMPT_OUTPUT_FORMAT = """
### Output Format
Return a JSON object with:
{
  "action": "ALLOW" | "PUSHBACK" | "DISTRACT" | "DELETE",
  "reasoning": "Brief explanation of your decision, referencing relevant strategies if applicable (e.g., 'Collective Action Potential', 'Strategic Distraction', 'Bayesian Persuasion').",
  "reply_content": "The response text (for PUSHBACK: argumentative counter-narrative; for DISTRACT: cheerful subject-change; for ALLOW/DELETE: null)"
}
"""

# Combine all components into the final system prompt
SYSTEM_PROMPT = f"{PROMPT_ROLE}\n{PROMPT_GAME_THEORY}\n{PROMPT_CENSORSHIP_STRATEGY}\n{PROMPT_POLICY_RULES}\n{PROMPT_OUTPUT_FORMAT}"

def evaluate_post(post_content):
    """
    Sends the post content to the LLM for censorship evaluation.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Post Content: \"{post_content}\""}
            ],
            temperature=0.2, # Low temperature for deterministic policy execution
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"


def process_csv(input_file, output_file):
    print(f"Reading from {input_file}...")
    with open(input_file, mode='r', encoding='utf-8') as infile, \
         open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.DictReader(infile)
        # Add new columns for the bot's output
        fieldnames = reader.fieldnames + ['action', 'reasoning', 'reply_content']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            content = row['content']
            print(f"Processing Post ID {row['post_id']}...")
            
            # Get response from LLM
            result_json_str = evaluate_post(content)
            
            # Parse JSON response
            try:
                result_data = json.loads(result_json_str)
                row['action'] = result_data.get('action', 'ERROR')
                row['reasoning'] = result_data.get('reasoning', 'Error parsing')
                row['reply_content'] = result_data.get('reply_content', '')
            except json.JSONDecodeError:
                row['action'] = "ERROR"
                row['reasoning'] = f"Failed to parse JSON: {result_json_str}"
                row['reply_content'] = ""
            except Exception as e:
                row['action'] = "ERROR"
                row['reasoning'] = f"Error: {str(e)}"
                row['reply_content'] = ""
            
            writer.writerow(row)
            
    print(f"\nFinished! Results written to {output_file}")

def process_random_posts_to_json(input_file, output_file, num_posts=20):
    """
    Process a random sample of posts from the input CSV and output results to JSON.
    Uses the original content for evaluation.
    """
    print(f"Reading posts from {input_file}...")
    
    # Read all posts
    with open(input_file, mode='r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        all_posts = list(reader)
    
    # Sample random posts
    if len(all_posts) < num_posts:
        print(f"Warning: Only {len(all_posts)} posts available, using all of them.")
        sample_posts = all_posts
    else:
        sample_posts = random.sample(all_posts, num_posts)
    
    print(f"Processing {len(sample_posts)} random posts...")
    
    results = []
    
    for idx, row in enumerate(sample_posts, 1):
        # Use original content for evaluation
        content = row.get('content', '')
        post_id = row.get('post_id', f'unknown_{idx}')
        
        print(f"Processing {idx}/{len(sample_posts)}: Post ID {post_id}...")
        
        # Get response from LLM
        result_json_str = evaluate_post(content)
        
        # Parse JSON response and add to results
        try:
            result_data = json.loads(result_json_str)
            result_entry = {
                'post_id': post_id,
                'original_content': content,
                'translated_content': row.get('content_translated', ''),
                'action': result_data.get('action', 'ERROR'),
                'reasoning': result_data.get('reasoning', 'Error parsing'),
                'reply_content': result_data.get('reply_content', None)
            }
        except json.JSONDecodeError:
            result_entry = {
                'post_id': post_id,
                'original_content': content,
                'translated_content': row.get('content_translated', ''),
                'action': 'ERROR',
                'reasoning': f'Failed to parse JSON: {result_json_str}',
                'reply_content': None
            }
        except Exception as e:
            result_entry = {
                'post_id': post_id,
                'original_content': content,
                'translated_content': row.get('content_translated', ''),
                'action': 'ERROR',
                'reasoning': f'Error: {str(e)}',
                'reply_content': None
            }
        
        results.append(result_entry)
    
    # Write to JSON file
    with open(output_file, 'w', encoding='utf-8') as outfile:
        json.dump(results, outfile, ensure_ascii=False, indent=2)
    
    print(f"\nFinished! Results written to {output_file}")
    return results

def process_top_themed_posts_to_json(input_file, output_file, num_posts_per_theme=30):
    """
    Process the top N posts for each theme score category and output results to JSON.
    Uses the original content for evaluation.
    """
    print(f"Reading posts from {input_file}...")
    
    # Read all posts
    with open(input_file, mode='r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        all_posts = list(reader)
    
    # Convert score columns to float for sorting
    for post in all_posts:
        try:
            post['theme_score_corruption'] = float(post.get('theme_score_corruption', 0))
            post['theme_score_nationalist'] = float(post.get('theme_score_nationalist', 0))
            post['theme_score_pro_freedom'] = float(post.get('theme_score_pro_freedom', 0))
        except (ValueError, TypeError):
            post['theme_score_corruption'] = 0
            post['theme_score_nationalist'] = 0
            post['theme_score_pro_freedom'] = 0
    
    # Get top posts for each theme
    top_corruption = sorted(all_posts, key=lambda x: x['theme_score_corruption'], reverse=True)[:num_posts_per_theme]
    top_nationalist = sorted(all_posts, key=lambda x: x['theme_score_nationalist'], reverse=True)[:num_posts_per_theme]
    top_pro_freedom = sorted(all_posts, key=lambda x: x['theme_score_pro_freedom'], reverse=True)[:num_posts_per_theme]
    
    # Combine all selected posts (may have duplicates, which is fine)
    themed_posts = {
        'corruption': top_corruption,
        'nationalist': top_nationalist,
        'pro_freedom': top_pro_freedom
    }
    
    results = {
        'corruption': [],
        'nationalist': [],
        'pro_freedom': []
    }
    
    for theme, posts in themed_posts.items():
        print(f"\nProcessing top {len(posts)} posts for theme: {theme}")
        
        for idx, row in enumerate(posts, 1):
            content = row.get('content', '')
            post_id = row.get('post_id', f'unknown_{idx}')
            
            print(f"Processing {idx}/{len(posts)} ({theme}): Post ID {post_id}...")
            
            # Get response from LLM
            result_json_str = evaluate_post(content)
            
            # Parse JSON response and add to results
            try:
                result_data = json.loads(result_json_str)
                result_entry = {
                    'post_id': post_id,
                    'original_content': content,
                    'translated_content': row.get('content_translated', ''),
                    'theme_score_corruption': row['theme_score_corruption'],
                    'theme_score_nationalist': row['theme_score_nationalist'],
                    'theme_score_pro_freedom': row['theme_score_pro_freedom'],
                    'action': result_data.get('action', 'ERROR'),
                    'reasoning': result_data.get('reasoning', 'Error parsing'),
                    'reply_content': result_data.get('reply_content', None)
                }
            except json.JSONDecodeError:
                result_entry = {
                    'post_id': post_id,
                    'original_content': content,
                    'translated_content': row.get('content_translated', ''),
                    'theme_score_corruption': row['theme_score_corruption'],
                    'theme_score_nationalist': row['theme_score_nationalist'],
                    'theme_score_pro_freedom': row['theme_score_pro_freedom'],
                    'action': 'ERROR',
                    'reasoning': f'Failed to parse JSON: {result_json_str}',
                    'reply_content': None
                }
            except Exception as e:
                result_entry = {
                    'post_id': post_id,
                    'original_content': content,
                    'translated_content': row.get('content_translated', ''),
                    'theme_score_corruption': row['theme_score_corruption'],
                    'theme_score_nationalist': row['theme_score_nationalist'],
                    'theme_score_pro_freedom': row['theme_score_pro_freedom'],
                    'action': 'ERROR',
                    'reasoning': f'Error: {str(e)}',
                    'reply_content': None
                }
            
            results[theme].append(result_entry)
    
    # Write to JSON file
    with open(output_file, 'w', encoding='utf-8') as outfile:
        json.dump(results, outfile, ensure_ascii=False, indent=2)
    
    print(f"\nFinished! Themed results written to {output_file}")
    return results


if __name__ == "__main__":
    # Process 100 random posts from the weiboscope file
    # process_random_posts_to_json(
    #     'weiboscope_week1_top900_translated_themed.csv',
    #     'censored_weibo_results1.json',
    #     num_posts=900
    # )   
    
    process_random_posts_to_json(
        'Weibo_Scope_901_to_1800_translated_themed.csv',
        'censored_weibo_results2.json',
        num_posts=900
    )   
    
    # Process top 30 posts for each theme
    # process_top_themed_posts_to_json(
    #     'weiboscope_week1_top900_translated_themed.csv',
    #     'censored_weibo_themed_results.json',
    #     num_posts_per_theme=30
    # )

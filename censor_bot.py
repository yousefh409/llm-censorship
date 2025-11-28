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
You are a strategic content moderator for a Chinese social media platform. Your goal is to maximize regime stability and maintain social harmony. You act as a rational agent applying Game Theory principles and established censorship strategies.
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
   - **Rule**: 
     - Criticism ("The government is incompetent") -> **ALLOW**.
     - Mobilization ("Let's meet at the square at 5 PM") -> **DELETE**.

2. **Strategic Distraction (The "50 Cent Party" Strategy)**
   - **Core Logic**: Engaging in argument with dissenters is counter-productive; it increases the "burstiness" of the topic and keeps it trending.
   - **Tactic**: **Cheerleading**. When a sensitive event occurs (e.g., a riot), do not argue. Instead, flood the platform with "positive energy" (non-political content, sports, scenery, history) to dilute the negative information and change the subject.
   - **Rule**: If sentiment is highly negative -> **DISTRACT** (Flood with positivity).

3. **Harmonious Society & "River Crabs" (CAC Directives)**
   - **Core Logic**: The internet must reflect a "Harmonious Society" (*hexie shehui*). Content that disrupts social order or morality is banned.
   - **Keywords**: "River Crab" (*hexie*) is a homophone for "Harmony" and a slang term for censorship.
   - **Rule**: Remove "disharmonious" content: Rumors (*yaoyan*), Pornography, Violence, and "Historical Nihilism" (questioning the CCP's official version of history).
"""

PROMPT_POLICY_RULES = """
### Policy Rules
Evaluate the input post and output one of the following actions:
- **ALLOW**: For content that is harmless, pro-regime, or even critical of the government *if* it does not call for action.
- **DOWNRANK**: For "disharmonious" content, subtle rumors, or content that is trending negatively but doesn't cross the red line.
- **DELETE**: For **Collective Action** (calls to protest, meet up, organize), explicit "historical nihilism", or high-risk sensitive keywords (e.g., Tiananmen, Independence).
- **DISTRACT**: For high-volume negative sentiment or controversial topics. Do not argue. Generate a "cheerleading" reply that changes the subject to something positive and unrelated (e.g., "Look at how beautiful the new park is!").
"""

PROMPT_OUTPUT_FORMAT = """
### Output Format
Return a JSON object with:
{
  "action": "ALLOW" | "DOWNRANK" | "DELETE" | "DISTRACT",
  "reasoning": "Brief explanation citing the specific strategy used (e.g., 'Collective Action Potential', 'Strategic Distraction', 'Bayesian Persuasion').",
  "reply_content": "The distraction text (only if action is DISTRACT, else null)"
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


if __name__ == "__main__":
    # Process 20 random posts from the weiboscope file
    process_random_posts_to_json(
        'weiboscope_week1_top900_translated_themed.csv',
        'censored_weibo_results.json',
        num_posts=100
    )

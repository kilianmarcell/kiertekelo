import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os
import numpy as np

def plot_comparisons():
    # Hardcoded to match the user's specific request "mindegyik modellhez csinálj régi és új tömböt is"
    plot_data = [
        {"Modell": "GPT-3.5 Turbo", "Korreláció": 0.381, "Kiértékelési mód": "Holisztikus"},
        {"Modell": "GPT-3.5 Turbo", "Korreláció": 0.451, "Kiértékelési mód": "Teszteset-alapú"},
        
        {"Modell": "GPT-4o", "Korreláció": 0.519, "Kiértékelési mód": "Holisztikus"},
        {"Modell": "GPT-4o", "Korreláció": 0.644, "Kiértékelési mód": "Teszteset-alapú"},
        
        {"Modell": "GPT-4o-mini", "Korreláció": 0.478, "Kiértékelési mód": "Holisztikus"},
        {"Modell": "GPT-4o-mini", "Korreláció": 0.752, "Kiértékelési mód": "Teszteset-alapú"},
        
        {"Modell": "Claude 3 Haiku", "Korreláció": 0.310, "Kiértékelési mód": "Holisztikus"},
        {"Modell": "Claude 3 Haiku", "Korreláció": 0.559, "Kiértékelési mód": "Teszteset-alapú"},
    ]
    
    df = pd.DataFrame(plot_data)
    
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(10, 6))
    
    ax = sns.barplot(data=df, x="Modell", y="Korreláció", hue="Kiértékelési mód", dodge=True, palette=["#3498db", "#2ecc71"])
    
    plt.title("Holisztikus és Teszteset-alapú kiértékelési módok összehasonlítása", fontsize=16, pad=15)
    plt.ylabel("Pearson Korreláció (r) a tanári pontozással", fontsize=12)
    plt.xlabel("", fontsize=12)
    plt.ylim(0, 1.0)
    plt.yticks(np.arange(0, 1.1, 0.1))
    
    for i, p in enumerate(ax.patches):
        height = p.get_height()
        if height > 0:
            ax.text(p.get_x() + p.get_width()/2., height + 0.02, f'{height:.3f}', ha='center')
            
    plt.legend(bbox_to_anchor=(0.5, -0.15), loc='upper center', ncol=2, frameon=False)
    plt.tight_layout()
    os.makedirs("docs/images", exist_ok=True)
    plt.savefig("docs/images/java_deck_comparison.png", dpi=300, bbox_inches='tight')
 
if __name__ == "__main__":
    plot_comparisons()

#!/usr/bin/env python3
"""
Model Validation Script for Netflix Recommendation System
Run this script to test if your model loads properly before deployment
"""

import os
import sys
import pickle
import gzip
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_model_loading():
    """Test model loading and validate structure"""
    print("=" * 60)
    print("Netflix Recommendation System - Model Validation Test")
    print("=" * 60)
    
    try:
        # Get model path
        app_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(app_dir, 'model.pkl.gz')
        
        print(f"📁 App directory: {app_dir}")
        print(f"📄 Model path: {model_path}")
        
        # Check if model file exists
        if not os.path.exists(model_path):
            print("❌ ERROR: Model file not found!")
            print(f"   Looking for: {model_path}")
            print(f"   Files in directory:")
            for file in os.listdir(app_dir):
                print(f"      - {file}")
            return False
            
        # Check file size
        file_size_mb = os.path.getsize(model_path) / (1024 * 1024)
        print(f"📏 Model file size: {file_size_mb:.2f} MB")
        
        if file_size_mb > 50:
            print("⚠️  WARNING: Model file is very large (>50MB)")
            print("   This may cause deployment issues on some platforms")
        
        # Test file reading permissions 
        if not os.access(model_path, os.R_OK):
            print("❌ ERROR: No read permission for model file!")
            return False
            
        print("📖 Loading model...")
        
        # Load the model
        with gzip.open(model_path, 'rb') as file:
            model_data = pickle.load(file)
        
        if model_data is None:
            print("❌ ERROR: Model data is None!")
            return False
            
        if not isinstance(model_data, dict):
            print(f"❌ ERROR: Invalid model data type: {type(model_data)}")
            return False
            
        print("✅ Model loaded successfully!")
        
        # Validate model structure
        print("🔍 Validating model structure...")
        
        required_keys = ['cosine_sim', 'netflix_data', 'indices']
        print(f"📋 Available keys: {list(model_data.keys())}")
        
        missing_keys = []
        for key in required_keys:
            if key not in model_data:
                missing_keys.append(key)
            else:
                print(f"   ✅ {key}")
                
        if missing_keys:
            print(f"❌ ERROR: Missing required keys: {missing_keys}")
            return False
            
        # Test dataset access
        try:
            netflix_data = model_data['netflix_data']
            cosine_sim = model_data['cosine_sim']
            indices = model_data['indices']
            
            print(f"📊 Dataset shape: {netflix_data.shape}")
            print(f"🔗 Cosine similarity matrix shape: {cosine_sim.shape}")
            print(f"📇 Number of title indices: {len(indices)}")
            print(f"🎬 Sample titles:")
            
            # Show sample titles
            for i, title in enumerate(netflix_data['title'].head(5)):
                print(f"      {i+1}. {title}")
                
            print("🧪 Testing recommendation function...")
            
            # Test a recommendation
            sample_title = netflix_data['title'].iloc[0]
            print(f"   Sample title: {sample_title}")
            
            # Simple recommendation test
            if sample_title.lower() in indices:
                print("   ✅ Title found in indices")
                idx = indices[sample_title.lower()]
                sim_scores = list(enumerate(cosine_sim[idx]))
                sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
                top_5 = sim_scores[1:6]  # Top 5 recommendations
                print("   📝 Top 5 recommendations:")
                for i, (movie_idx, score) in enumerate(top_5, 1):
                    rec_title = netflix_data['title'].iloc[movie_idx]
                    print(f"      {i}. {rec_title} (Score: {score:.4f})")
            else:
                print("   ⚠️  Sample title not found in indices")
                
        except Exception as e:
            print(f"❌ ERROR: Problem accessing model components: {e}")
            return False
            
        print("🎉 All tests passed! Model is ready for deployment.")
        return True
        
    except Exception as e:
        print(f"❌ FATAL ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_model_loading()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ RESULT: Model validation PASSED")
        print("   Your model should work properly on deployment platforms.")
    else:
        print("❌ RESULT: Model validation FAILED") 
        print("   Please fix the issues above before deploying.")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
"""Download and manage official benchmark datasets"""

import os
import json
import requests
from typing import Dict, List, Any
from pathlib import Path


class BenchmarkDownloader:
    """Download and manage official benchmark datasets"""
    
    DATASETS = {
        'humaneval': {
            'url': 'https://github.com/openai/human-eval/raw/master/data/HumanEval.jsonl.gz',
            'file': 'HumanEval.jsonl.gz',
            'description': 'OpenAI HumanEval - 164 Python programming problems',
            'size': '~100KB',
            'license': 'MIT'
        },
        'mbpp': {
            'url': 'https://github.com/google-research/google-research/raw/master/mbpp/mbpp.jsonl',
            'file': 'mbpp.jsonl',
            'description': 'Google MBPP - 974 Python programming problems',
            'size': '~2MB',
            'license': 'Apache 2.0'
        },
        'humaneval_plus': {
            'url': 'https://github.com/evalplus/evalplus/releases/download/v0.2.0/HumanEvalPlus.jsonl.gz',
            'file': 'HumanEvalPlus.jsonl.gz',
            'description': 'HumanEval+ - Enhanced version with more test cases',
            'size': '~500KB',
            'license': 'MIT'
        },
        'mbpp_plus': {
            'url': 'https://github.com/evalplus/evalplus/releases/download/v0.2.0/MbppPlus.jsonl.gz',
            'file': 'MbppPlus.jsonl.gz',
            'description': 'MBPP+ - Enhanced version with more test cases',
            'size': '~5MB',
            'license': 'Apache 2.0'
        }
    }
    
    def __init__(self, data_dir: str = "benchmarks"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
    
    def list_available_datasets(self) -> Dict[str, Dict[str, str]]:
        """List all available datasets for download"""
        return self.DATASETS.copy()
    
    def is_downloaded(self, dataset_name: str) -> bool:
        """Check if a dataset is already downloaded"""
        if dataset_name not in self.DATASETS:
            return False
        
        dataset_info = self.DATASETS[dataset_name]
        file_path = self.data_dir / dataset_info['file']
        
        # Also check for extracted version
        if dataset_info['file'].endswith('.gz'):
            extracted_path = self.data_dir / dataset_info['file'][:-3]
            return file_path.exists() or extracted_path.exists()
        
        return file_path.exists()
    
    def download_dataset(self, dataset_name: str, force: bool = False) -> bool:
        """Download a specific dataset"""
        if dataset_name not in self.DATASETS:
            raise ValueError(f"Unknown dataset: {dataset_name}")
        
        dataset_info = self.DATASETS[dataset_name]
        file_path = self.data_dir / dataset_info['file']
        
        if file_path.exists() and not force:
            print(f"Dataset {dataset_name} already exists. Use force=True to re-download.")
            return True
        
        try:
            print(f"Downloading {dataset_name} from {dataset_info['url']}...")
            
            response = requests.get(dataset_info['url'], stream=True)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ Downloaded {dataset_name} to {file_path}")
            
            # Extract if gzipped
            if file_path.suffix == '.gz':
                self._extract_gzip(file_path)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to download {dataset_name}: {e}")
            if file_path.exists():
                file_path.unlink()  # Clean up partial download
            return False
    
    def _extract_gzip(self, file_path: Path) -> bool:
        """Extract gzipped file"""
        try:
            import gzip
            
            extracted_path = file_path.with_suffix('')
            
            with gzip.open(file_path, 'rb') as f_in:
                with open(extracted_path, 'wb') as f_out:
                    f_out.write(f_in.read())
            
            print(f"✅ Extracted to {extracted_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to extract {file_path}: {e}")
            return False
    
    def get_dataset_info(self, dataset_name: str) -> Dict[str, Any]:
        """Get detailed information about a dataset"""
        if dataset_name not in self.DATASETS:
            raise ValueError(f"Unknown dataset: {dataset_name}")
        
        info = self.DATASETS[dataset_name].copy()
        info['downloaded'] = self.is_downloaded(dataset_name)
        
        if info['downloaded']:
            # Get file stats
            file_path = self.data_dir / info['file']
            if info['file'].endswith('.gz'):
                extracted_path = self.data_dir / info['file'][:-3]
                if extracted_path.exists():
                    file_path = extracted_path
            
            if file_path.exists():
                stat = file_path.stat()
                info['local_size'] = f"{stat.st_size / 1024:.1f}KB"
                info['local_path'] = str(file_path)
                
                # Count problems if it's a JSONL file
                if file_path.suffix == '.jsonl':
                    try:
                        with open(file_path, 'r') as f:
                            info['problem_count'] = sum(1 for _ in f)
                    except:
                        info['problem_count'] = 'Unknown'
        
        return info
    
    def download_all(self, force: bool = False) -> Dict[str, bool]:
        """Download all available datasets"""
        results = {}
        
        for dataset_name in self.DATASETS:
            print(f"\n📥 Downloading {dataset_name}...")
            results[dataset_name] = self.download_dataset(dataset_name, force)
        
        return results
    
    def get_dataset_path(self, dataset_name: str) -> Path:
        """Get the local path for a dataset"""
        if dataset_name not in self.DATASETS:
            raise ValueError(f"Unknown dataset: {dataset_name}")
        
        if not self.is_downloaded(dataset_name):
            raise FileNotFoundError(f"Dataset {dataset_name} not downloaded")
        
        dataset_info = self.DATASETS[dataset_name]
        file_path = self.data_dir / dataset_info['file']
        
        # Check for extracted version
        if dataset_info['file'].endswith('.gz'):
            extracted_path = self.data_dir / dataset_info['file'][:-3]
            if extracted_path.exists():
                return extracted_path
        
        return file_path
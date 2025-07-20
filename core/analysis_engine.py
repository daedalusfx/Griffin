import logging
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from influxdb_client import InfluxDBClient
from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal

class AnalysisEngine(QObject):
    """
    Handles all data processing and machine learning logic.
    Emits signals to communicate with the main GUI thread.
    """
    # Signal now emits two DataFrames: the report and the data for plotting
    finished = pyqtSignal(pd.DataFrame, pd.DataFrame)
    progress = pyqtSignal(int, str)
    error = pyqtSignal(str)
    metadata_found = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.settings = {}

    @pyqtSlot(dict)
    def fetch_metadata(self, settings):
        """Fetches available brokers, symbols, and timeframes from the database."""
        try:
            self.progress.emit(20, "Connecting to DB to fetch metadata...")
            metadata = {'brokers': [], 'symbols': [], 'timeframes': []}
            with InfluxDBClient(url=settings['url'], token=settings['token'], org=settings['org']) as client:
                query_api = client.query_api()
                def get_tag_values(tag_name):
                    query = f'import "influxdata/influxdb/schema" schema.tagValues(bucket: "{settings["bucket"]}", tag: "{tag_name}")'
                    tables = query_api.query(query)
                    return [record.get_value() for table in tables for record in table.records]

                self.progress.emit(40, "Fetching brokers...")
                metadata['brokers'] = get_tag_values("broker")
                self.progress.emit(60, "Fetching symbols...")
                metadata['symbols'] = get_tag_values("symbol")
                self.progress.emit(80, "Fetching timeframes...")
                metadata['timeframes'] = get_tag_values("period")

            if not metadata['brokers']: raise ValueError("No brokers found.")
            self.progress.emit(100, "Metadata fetched successfully.")
            self.metadata_found.emit(metadata)
        except Exception as e:
            logging.error(f"Metadata fetch failed: {e}", exc_info=True)
            self.error.emit(f"Metadata fetch failed: {e}")

    @pyqtSlot(dict)
    def run_analysis(self, settings):
        """Main method to run the full analysis pipeline."""
        try:
            self.settings = settings
            self.progress.emit(5, "Connecting to InfluxDB...")
            data_df = self._get_data()

            self.progress.emit(25, "Extracting features...")
            features_df = self._extract_ohlc_features(data_df)

            if len(features_df) < self.settings['min_brokers']:
                raise ValueError(f"Clustering requires at least {self.settings['min_brokers']} brokers.")

            self.progress.emit(50, "Performing clustering...")
            result_df = self._perform_clustering(features_df)

            self.progress.emit(75, "Preparing visualization data...")
            profile_map = self._interpret_clusters(result_df)
            final_report = result_df.copy()
            final_report['Profile'] = final_report['Cluster'].map(profile_map)
            final_report.sort_values('Cluster', inplace=True)
            
            pca_df_for_plot = self._prepare_visualization_data(result_df, profile_map)

            self.progress.emit(100, "Analysis complete.")
            self.finished.emit(final_report, pca_df_for_plot)
        except Exception as e:
            logging.error(f"Analysis failed: {e}", exc_info=True)
            self.error.emit(str(e))

    def _get_data(self):
        """Fetches and preprocesses data from InfluxDB."""
        with InfluxDBClient(url=self.settings['url'], token=self.settings['token'], org=self.settings['org']) as client:
            brokers_filter = ' or '.join([f'r["broker"] == "{b}"' for b in self.settings['brokers']])
            flux_query = fr'''
            from(bucket: "{self.settings['bucket']}")
              |> range(start: -30d)
              |> filter(fn: (r) => r["_measurement"] == "price" and ({brokers_filter}))
              |> filter(fn: (r) => r["_field"] == "close" or r["_field"] == "high" or r["_field"] == "low" or r["_field"] == "open")
              |> filter(fn: (r) => r["period"] == "{self.settings['timeframe']}" and r["symbol"] == "{self.settings['symbol']}")
              |> aggregateWindow(every: 1h, fn: last, createEmpty: false)
            '''
            df_raw = client.query_api().query_data_frame(query=flux_query)
            if df_raw.empty: raise ValueError("Query returned no data.")

            df_pivot = df_raw.pivot(index=['_time', 'broker'], columns='_field', values='_value').reset_index()
            required_cols = ['open', 'high', 'low', 'close']
            df_pivot.dropna(subset=required_cols, inplace=True)
            for col in required_cols: df_pivot[col] = pd.to_numeric(df_pivot[col], errors='coerce')
            df_pivot.dropna(subset=required_cols, inplace=True)
            if df_pivot.empty: raise ValueError("No valid OHLC data remained after cleaning.")
            return df_pivot

    def _extract_ohlc_features(self, df):
        features_list = []
        for broker in df['broker'].unique():
            broker_df = df[df['broker'] == broker].copy().sort_values('_time')
            if len(broker_df) < self.settings['min_points']: continue
            gap = np.abs(broker_df['open'] - broker_df['close'].shift(1))
            high_low = broker_df['high'] - broker_df['low']
            body_size = np.abs(broker_df['open'] - broker_df['close']) + 1e-9
            spike_ratio = high_low / body_size
            features_list.append({
                'broker': broker, 'Gap_Median': gap.median(), 'Spike_Median': spike_ratio.median(),
                'Spike_Max': spike_ratio.max(), 'Gap_Max': gap.max()
            })
        if not features_list: raise ValueError(f"No broker had enough data.")
        return pd.DataFrame(features_list).set_index('broker')

    def _perform_clustering(self, features_df):
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features_df)
        
        inertias = []
        max_clusters = min(len(features_scaled), 8)
        optimal_k = 1
        if max_clusters > 1:
            for k in range(1, max_clusters + 1):
                kmeans = KMeans(n_clusters=k, random_state=42, n_init='auto').fit(features_scaled)
                inertias.append(kmeans.inertia_)
            try:
                deltas = np.diff(inertias, 2)
                optimal_k = np.argmax(deltas) + 2
            except ValueError:
                optimal_k = max_clusters // 2
        
        kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init='auto')
        result_df = features_df.copy()
        result_df['Cluster'] = kmeans.fit_predict(features_scaled)
        return result_df

    def _interpret_clusters(self, result_df):
        cluster_profiles = result_df.groupby('Cluster').mean()
        cluster_profiles['Gap_Rank'] = cluster_profiles['Gap_Median'].rank()
        cluster_profiles['Spike_Rank'] = cluster_profiles['Spike_Median'].rank()
        cluster_profiles['Overall_Rank'] = cluster_profiles['Gap_Rank'] + cluster_profiles['Spike_Rank']
        quality_map = {1: "Excellent Quality", 2: "Good Quality", 3: "Standard Quality", 4: "High Risk"}
        cluster_profiles['Profile_Name'] = cluster_profiles['Overall_Rank'].rank(method='dense').map(quality_map).fillna("General")
        return cluster_profiles['Profile_Name'].to_dict()

    def _prepare_visualization_data(self, result_df, profile_map):
        """Prepares the DataFrame for plotting in the GUI."""
        pca = PCA(n_components=2)
        features_scaled = StandardScaler().fit_transform(result_df.drop(columns=['Cluster']))
        components = pca.fit_transform(features_scaled)
        
        pca_df = pd.DataFrame(data=components, columns=['PC1', 'PC2'], index=result_df.index)
        pca_df['Cluster'] = result_df['Cluster']
        pca_df['Profile'] = pca_df['Cluster'].map(profile_map)
        
        # Attach explained variance info to the DataFrame's attributes
        pca_df.attrs['explained_variance'] = pca.explained_variance_ratio_
        return pca_df

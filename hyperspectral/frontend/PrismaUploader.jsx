import React, { useState } from 'react';

const PrismaUploader = () => {
    const [file, setFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [statusMessage, setStatusMessage] = useState('');

    // Taille de chaque morceau : 5 Mo (ajustable selon la qualité de la connexion)
    const CHUNK_SIZE = 5 * 1024 * 1024;

    const handleFileChange = (e) => {
        if (e.target.files.length > 0) {
            setFile(e.target.files[0]);
            setProgress(0);
            setStatusMessage('');
        }
    };

    const uploadFileInChunks = async () => {
        if (!file) {
            setStatusMessage('⚠️ Veuillez sélectionner un fichier PRISMA HDF5.');
            return;
        }

        setUploading(true);
        setStatusMessage('Connexion établie. Début du transfert hyperspectral...');

        const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
        const fileId = crypto.randomUUID(); // Identifiant unique pour ce transfert binaire

        // Boucle séquentielle pour garantir l'écriture ordonnée sur le disque (FastAPI)
        for (let currentChunkIndex = 0; currentChunkIndex < totalChunks; currentChunkIndex++) {

            // 1. Découpage du fichier avec l'API native File.slice()
            const start = currentChunkIndex * CHUNK_SIZE;
            const end = Math.min(start + CHUNK_SIZE, file.size);
            const chunkBlob = file.slice(start, end);

            // 2. Construction du conteneur Multipart FormData
            const formData = new FormData();
            formData.append('file', chunkBlob, file.name);
            formData.append('chunk_index', currentChunkIndex);
            formData.append('total_chunks', totalChunks);
            formData.append('file_id', fileId);
            formData.append('filename', file.name);

            try {
                // 3. Envoi de la requête HTTP POST
                const response = await fetch('http://localhost:8000/upload-prisma-chunk', {
                    method: 'POST',
                    body: formData,
                });

                if (!response.ok) {
                    throw new Error(`Erreur HTTP au chunk ${currentChunkIndex}`);
                }

                const result = await response.json();

                // 4. Calcul et mise à jour de la progression globale
                const currentProgress = Math.round(((currentChunkIndex + 1) / totalChunks) * 100);
                setProgress(currentProgress);
                setStatusMessage(`Transfert en cours : morceau ${currentChunkIndex + 1} / ${totalChunks}`);

                // Si c'est le dernier morceau, le backend nous renvoie le chemin final
                if (result.status === 'completed') {
                    setStatusMessage(`✅ Fichier assemblé avec succès sur GeoCongo AI. Chemin : ${result.filepath}`);
                    setUploading(false);
                    // Optionnel : déclencher automatiquement la route '/process-prisma' ici
                }

            } catch (error) {
                console.error('Échec du transfert :', error);
                setStatusMessage(`❌ Erreur lors de l'envoi du morceau ${currentChunkIndex + 1}. Relancez le transfert.`);
                setUploading(false);
                return; // Arrêt complet du pipeline en cas de rupture de flux
            }
        }
    };

    return (
        <div style={{ padding: '20px', maxWidth: '500px', margin: '0 auto', fontFamily: 'Arial, sans-serif' }}>
            <h2 style={{ color: '#2c3e50' }}>GeoCongo AI HyperSpectral</h2>
            <h3 style={{ color: '#34495e', fontWeight: 'normal' }}>Chargement de Scènes PRISMA L2D</h3>

            <div style={{ marginBottom: '15px' }}>
                <input
                    type="file"
                    accept=".h5,.he5"
                    onChange={handleFileChange}
                    disabled={uploading}
                    style={{ width: '100%', padding: '10px', border: '1px solid #ddd', borderRadius: '4px' }}
                />
            </div>

            <button
                onClick={uploadFileInChunks}
                disabled={uploading || !file}
                style={{
                    width: '100%',
                    padding: '12px 20px',
                    backgroundColor: uploading ? '#bdc3c7' : '#2980b9',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '16px',
                    transition: 'background 0.3s'
                }}
            >
                {uploading ? 'Analyse en cours...' : 'Lancer le Chunked Upload'}
            </button>

            {uploading || progress > 0 ? (
                <div style={{ marginTop: '20px' }}>
                    <div style={{ width: '100%', backgroundColor: '#f0f3f4', borderRadius: '4px', height: '20px', overflow: 'hidden' }}>
                        <div
                            style={{
                                width: `${progress}%`,
                                backgroundColor: '#27ae60',
                                height: '100%',
                                transition: 'width 0.2s ease-in-out',
                                textAlign: 'center',
                                color: '#fff',
                                fontSize: '12px',
                                lineHeight: '20px'
                            }}
                        >
                            {progress}%
                        </div>
                    </div>
                </div>
            ) : null}

            {statusMessage && (
                <p style={{
                    marginTop: '15px',
                    fontSize: '14px',
                    color: statusMessage.includes('✅') ? '#27ae60' : (statusMessage.includes('❌') ? '#e74c3c' : '#7f8c8d'),
                    fontWeight: '500',
                    backgroundColor: '#f8f9fa',
                    padding: '10px',
                    borderRadius: '4px',
                    borderLeft: '4px solid'
                }}>
                    {statusMessage}
                </p>
            )}
        </div>
    );
};

export default PrismaUploader;

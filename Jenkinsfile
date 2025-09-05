pipeline {
    agent any
    
    environment {
        REGISTRY = 'ghcr.io'
        IMAGE_NAME = 'your-org/telemetry'
        KUBECONFIG = '/opt/telemetry/.kube/config'
        HELM_RELEASE_NAME = 'telemetry'
        HELM_NAMESPACE = 'telemetry'
    }
    
    parameters {
        string(name: 'GIT_TAG', defaultValue: '', description: 'Git tag for deployment (e.g., v1.0.0)')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    if (params.GIT_TAG) {
                        sh "git checkout ${params.GIT_TAG}"
                        env.GIT_TAG = params.GIT_TAG
                    } else {
                        env.GIT_TAG = sh(
                            script: 'git describe --tags --always',
                            returnStdout: true
                        ).trim()
                    }
                }
            }
        }
        
        stage('Build & Push') {
            when {
                anyOf {
                    tag pattern: "v\\d+\\.\\d+\\.\\d+", comparator: "REGEXP"
                    params.GIT_TAG
                }
            }
            steps {
                script {
                    def services = ['generator', 'collector', 'processor']
                    
                    services.each { service ->
                        stage("Build ${service}") {
                            sh """
                                docker build -t ${REGISTRY}/${IMAGE_NAME}-${service}:${env.GIT_TAG} \
                                    -t ${REGISTRY}/${IMAGE_NAME}-${service}:latest \
                                    ./services/telemetry-${service}/
                            """
                        }
                        
                        stage("Push ${service}") {
                            withCredentials([usernamePassword(credentialsId: 'ghcr-credentials', usernameVariable: 'REGISTRY_USER', passwordVariable: 'REGISTRY_TOKEN')]) {
                                sh """
                                    echo \$REGISTRY_TOKEN | docker login ${REGISTRY} -u \$REGISTRY_USER --password-stdin
                                    docker push ${REGISTRY}/${IMAGE_NAME}-${service}:${env.GIT_TAG}
                                    docker push ${REGISTRY}/${IMAGE_NAME}-${service}:latest
                                """
                            }
                        }
                    }
                }
            }
        }
        
        stage('Deploy') {
            when {
                anyOf {
                    tag pattern: "v\\d+\\.\\d+\\.\\d+", comparator: "REGEXP"
                    params.GIT_TAG
                }
            }
            steps {
                script {
                    withCredentials([kubeconfigFile(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                        sh """
                            helm upgrade --install ${HELM_RELEASE_NAME} ./k8s/helm/ \
                                --namespace ${HELM_NAMESPACE} \
                                --create-namespace \
                                --set image.tag=${env.GIT_TAG} \
                                --set image.repositoryPrefix=${REGISTRY}/${IMAGE_NAME}- \
                                --wait --timeout=10m
                        """
                    }
                }
            }
        }
        
        stage('Smoke Tests') {
            when {
                anyOf {
                    tag pattern: "v\\d+\\.\\d+\\.\\d+", comparator: "REGEXP"
                    params.GIT_TAG
                }
            }
            steps {
                script {
                    withCredentials([kubeconfigFile(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                        sh """
                            kubectl wait --for=condition=ready pod -l app=collector -n ${HELM_NAMESPACE} --timeout=300s
                            kubectl wait --for=condition=ready pod -l app=processor -n ${HELM_NAMESPACE} --timeout=300s
                            kubectl wait --for=condition=ready pod -l app=generator -n ${HELM_NAMESPACE} --timeout=300s
                        """
                        
                        // Test health endpoints
                        sh """
                            kubectl get pods -n ${HELM_NAMESPACE}
                            
                            # Test collector health
                            kubectl exec -n ${HELM_NAMESPACE} deployment/collector -- curl -f http://localhost:8080/health || exit 1
                            
                            # Test processor health
                            kubectl exec -n ${HELM_NAMESPACE} deployment/processor -- curl -f http://localhost:8000/health || exit 1
                            
                            # Test generator health
                            kubectl exec -n ${HELM_NAMESPACE} deployment/generator -- curl -f http://localhost:9100/health || exit 1
                        """
                        
                        // Test metrics endpoints
                        sh """
                            # Test collector metrics
                            kubectl exec -n ${HELM_NAMESPACE} deployment/collector -- curl -f http://localhost:8080/metrics | grep telemetry_collected_total || exit 1
                            
                            # Test processor metrics
                            kubectl exec -n ${HELM_NAMESPACE} deployment/processor -- curl -f http://localhost:8000/metrics | grep telemetry_processed_total || exit 1
                            
                            # Test generator metrics
                            kubectl exec -n ${HELM_NAMESPACE} deployment/generator -- curl -f http://localhost:9100/metrics | grep telemetry_generated_total || exit 1
                        """
                    }
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            echo "Pipeline completed successfully for tag: ${env.GIT_TAG}"
        }
        failure {
            echo "Pipeline failed for tag: ${env.GIT_TAG}"
        }
    }
}

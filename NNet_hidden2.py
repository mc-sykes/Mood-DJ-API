import numpy as np
import matplotlib.pyplot as plt

class NeuralNet():
    '''
    A two layer neural network
    '''
        
    def __init__(self, layers=[13,8,8,1], learning_rate=0.001, iterations=100):
        self.initialized = False
        self.params = {}
        self.layers = layers
        self.learning_rate = learning_rate
        self.iterations = iterations
        self.loss = []
        self.sample_size = None
        self.X = None
        self.y = None
                
    def init_weights(self):
        '''
        Initialize the weights from a random normal distribution
        '''
        #np.random.seed(1) # Seed the random number generator
        self.params["W1"] = np.random.randn(self.layers[0], self.layers[1]) 
        self.params['b1']  =np.random.randn(self.layers[1],)
        self.params['W2'] = np.random.randn(self.layers[1],self.layers[2]) 
        self.params['b2'] = np.random.randn(self.layers[2],)
        self.params['W3'] = np.random.randn(self.layers[2],self.layers[3]) 
        self.params['b3'] = np.random.randn(self.layers[3],)
        self.initialized = True
        
    def relu(self,Z): #elu
        '''
        The ReLufunction performs a threshold
        operation to each input element where values less 
        than zero are set to zero.
        '''
        #r = lambda x: (a*(np.exp(x)-1)) if x<0 else x
        a = 0.3
        z = [(a*(np.exp(y)-1)) if y<0 else y for x in Z for y in x]
        z = np.reshape(z, (Z.shape[0],Z.shape[1]))
        z = np.stack(z)
        return z
        #return np.maximum(0, Z)
        
        
    def sigmoid(self,Z):
        '''
        The sigmoid function takes in real numbers in any range and 
        squashes it to a real-valued output between 0 and 1.
        '''
        return 1.0 / (1.0 + np.exp(-Z))
    
    def entropy_loss(self,y, yhat):
        nsample = len(y)
        loss = -1/nsample * (np.sum(np.multiply(np.log(yhat), y) + np.multiply((1 - y), np.log(1 - yhat))))
        return loss

    
    def forward_propagation(self):
        '''
        Performs the forward propagation
        '''
        
        Z1 = self.X.dot(self.params['W1']) + self.params['b1']
        A1 = self.relu(Z1)
        Z2 = A1.dot(self.params['W2']) + self.params['b2']
        A2 = self.relu(Z2)
        Z3 = A2.dot(self.params['W3']) + self.params['b3']
        yhat = self.sigmoid(Z3)
        loss = self.entropy_loss(self.y,yhat)

        # save calculated parameters     
        self.params['Z1'] = Z1
        self.params['Z2'] = Z2
        self.params['Z3'] = Z3
        self.params['A1'] = A1
        self.params['A2'] = A2

        return yhat,loss

    
    def back_propagation(self,yhat):
        '''
        Computes the derivatives and update weights and bias according.
        '''
        def dRelu(Z):

            '''x[x<=0] = 0
            x[x>0] = 1'''
            z = [(dReluHelper(y)+0.3) if y<=0 else 1 for x in Z for y in x]
            z = np.reshape(z, (Z.shape[0],Z.shape[1]))
            z = np.stack(z)
            return z
        def dReluHelper(x):
            if x<0:
                x = 0.3*(np.exp(x)-1)
            return x
        
        dl_wrt_yhat = -(np.divide(self.y,yhat) - np.divide((1 - self.y),(1-yhat)))
        dl_wrt_sig = yhat * (1-yhat)
        dl_wrt_z3 = dl_wrt_yhat * dl_wrt_sig

        dl_wrt_A2 = dl_wrt_z3.dot(self.params['W3'].T)
        dl_wrt_w3 = self.params['A2'].T.dot(dl_wrt_z3)
        dl_wrt_b3 = np.sum(dl_wrt_z3, axis=0)
        dl_wrt_z2 = dl_wrt_A2 * dRelu(self.params['Z2'])

        dl_wrt_A1 = dl_wrt_z2.dot(self.params['W2'].T)
        dl_wrt_w2 = self.params['A1'].T.dot(dl_wrt_z2)
        dl_wrt_b2 = np.sum(dl_wrt_z2, axis=0)
        dl_wrt_z1 = dl_wrt_A1 * dRelu(self.params['Z1'])

        dl_wrt_w1 = self.X.T.dot(dl_wrt_z1)
        dl_wrt_b1 = np.sum(dl_wrt_z1, axis=0)

        #update the weights and bias
        self.params['W1'] = self.params['W1'] - self.learning_rate * dl_wrt_w1
        self.params['W2'] = self.params['W2'] - self.learning_rate * dl_wrt_w2
        self.params['W3'] = self.params['W3'] - self.learning_rate * dl_wrt_w3
        self.params['b1'] = self.params['b1'] - self.learning_rate * dl_wrt_b1
        self.params['b2'] = self.params['b2'] - self.learning_rate * dl_wrt_b2
        self.params['b3'] = self.params['b3'] - self.learning_rate * dl_wrt_b3

        
    def fit(self, X, y):
        '''
        Trains the neural network using the specified data and labels
        '''
        self.X = X
        self.y = y
        if(not self.initialized):
            self.init_weights() #initialize weights and bias


        for i in range(self.iterations):
            yhat, loss = self.forward_propagation()
            self.back_propagation(yhat)
            self.loss.append(loss)
            if i%(int(self.iterations/10))==0:
                print(i)
            
            
    def predict(self, X):
        '''
        Predicts on a test data
        '''
        Z1 = X.dot(self.params['W1']) + self.params['b1']
        A1 = self.relu(Z1)
        Z2 = A1.dot(self.params['W2']) + self.params['b2']
        A2 = self.relu(Z2)
        Z3 = A2.dot(self.params['W3']) + self.params['b3']
        pred = self.sigmoid(Z3)
        #new stuff
        '''guess = pred
        for i in range(len(guess)):
            if guess[i] <.2:
                guess[i] = 0
            elif guess[i] <.4:
                guess[i] = 1
            elif guess[i] <.6:
                guess[i] = 2
            elif guess[i] <.8:
                guess[i] = 3
            else:
                guess[i] = 4'''
        return pred              

                                
    def acc(self, y, yhat): # needs fix
        '''
        Calculates the accutacy between the predicted valuea and the truth labels
        '''
        '''
        correctOnes = 0
        ttlCorrect = 0
        totalOnes = 0
        #will prob need two loops, one for columns, one for rows
        for col in range(y.shape[1]):
            for row in range(len(y)):
                if y[row][col] == yhat[row][col]:
                    ttlCorrect += 1
                if y[row][col] == 1 and int(yhat[row][col]) == 1:
                    correctOnes += 1
                elif y[row][col] == 1 or int(yhat[row][col]) == 1:
                    totalOnes += 1
        acc = int((ttlCorrect/(len(y)*5))*100)
        really = int((correctOnes/totalOnes)*100)
        return acc, really'''
        acc = int(sum(y == yhat) / len(y) * 100)
        return acc



    def plot_loss(self):
        '''
        Plots the loss curve
        '''
        plt.plot(self.loss)
        plt.xlabel("Iteration")
        plt.ylabel("logloss")
        plt.title("Loss curve for training")
        plt.show()
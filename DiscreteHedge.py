#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Discrete hedge simulation
For 1.4
"""
import numpy as np

import Helpers.SimulateProcess as sim
from Options.base import claim
from Options.binary import binary

def SimulateSimpleDeltaHedge(stockSim : np.ndarray, option : claim,K,T,r,sigma):
    m, n = stockSim.shape
    matTime = T - np.arange(0,m).reshape(-1, 1)*T/(m-1)
    pfV = np.zeros((m, n))
    pfS = np.zeros((m, n))
    pfB = np.zeros((m, n))
    pfV[0] = option.price(option, S=stockSim[0],K=K,T=T,r=r,sigma=sigma)
    pfS = option.delta(option,S=stockSim,K=K,T=matTime,r=r,sigma=sigma)
    
    interest = np.exp(r*matTime[-2])

    for i in range(1,m):
        pfB[i-1] = pfV[i-1]-pfS[i-1]*stockSim[i-1]
        pfV[i] = pfS[i-1]*stockSim[i] + pfB[i-1]* interest
        
    pfO = option.payoff(option, S=stockSim[-1],K=K)
    discountedHedgeError = (pfV[-1]-pfO) * np.exp(-r*T)
    return {'discounted hedge error' : discountedHedgeError, 
            'option payoff' : pfO, 
            'hedging pf value' : pfV[-1],
            'hedging pf path' : pfV, 
            'hedging pf S' : pfS, 
            'hedging pf B' : pfB}

def SimulateBadForeignDeltaHedge(Brownian2D : np.ndarray, option : claim, X0, S0, T, rD,rF, sigmaF,sigmaX, **v):
    p, n, m = Brownian2D.shape
    
    if p != 2:
        raise ValueError(f"Expected 2 in dim 1 of simulations, recieved {p}")
        
    t = np.arange(0,n).reshape(-1, 1)*T/(n-1)                                 
    matTime = T - t
    
    stockSim = S0 * np.exp((rF-np.dot(sigmaX.T,sigmaF)-1/2*np.dot(sigmaF.T,sigmaF))*t+np.dot(sigmaF.T,np.transpose(Brownian2D,(1,0,2))))
    exchSim = X0 * np.exp((rD-rF-1/2*np.dot(sigmaX.T,sigmaX))*t+np.dot(sigmaX.T,np.transpose(Brownian2D,(1,0,2))))
    
    pfV = np.zeros((n, m))
    pfS = np.zeros((n, m))
    pfBD = np.zeros((n, m))
    
    pfV[0] = option.price(S=stockSim[0],T=T,rD=rD,rF=rF,sigmaF=sigmaF,sigmaX=sigmaX, **v)
    pfS = option.delta(S=stockSim,T=matTime,rD=rD,rF=rF,sigmaF=sigmaF,sigmaX=sigmaX, **v)/exchSim
    
    interest = np.exp(rD*matTime[-2])

    for i in range(1,n):
        pfBD[i-1] = pfV[i-1]-pfS[i-1]*stockSim[i-1]*exchSim[i-1]
        pfV[i] = pfS[i-1]*stockSim[i]*exchSim[i] + pfBD[i-1]* interest
    
    pfO = option.payoff(S=stockSim[-1], **v)
    discountedHedgeError = (pfV[-1]-pfO) * np.exp(-rD*T)
    return {'discounted hedge error' : discountedHedgeError, 
            'option payoff' : pfO, 
            'hedging pf value' : pfV[-1],
            'hedging pf path' : pfV, 
            'hedging pf S' : pfS, 
            'hedging pf BD' : pfBD,
            'asset value': stockSim[-1]}


def SimulateGoodForeignDeltaHedge(Brownian2D : np.ndarray, option : claim, X0, S0, T, rD,rF, sigmaF,sigmaX, **v):
    p, n, m = Brownian2D.shape
    
    if p != 2:
        raise ValueError(f"Expected 2 in dim 1 of simulations, recieved {p}")
        
    t = np.arange(0,n).reshape(-1, 1)*T/(n-1)                                 
    matTime = T - t
    
    stockSim = S0 * np.exp((rF-np.dot(sigmaX.T,sigmaF)-1/2*np.dot(sigmaF.T,sigmaF))*t+np.dot(sigmaF.T,np.transpose(Brownian2D,(1,0,2))))
    exchSim = X0 * np.exp((rD-rF-1/2*np.dot(sigmaX.T,sigmaX))*t+np.dot(sigmaX.T,np.transpose(Brownian2D,(1,0,2))))
    
    pfV = np.zeros((n, m))
    pfS = np.zeros((n, m))
    pfBD = np.zeros((n, m))
    pfBF = np.zeros((n, m))
    
    pfV[0] = option.price(S=stockSim[0],T=T,rD=rD,rF=rF,sigmaF=sigmaF,sigmaX=sigmaX, **v)
    pfS = option.delta(S=stockSim,T=matTime,rD=rD,rF=rF,sigmaF=sigmaF,sigmaX=sigmaX, **v)/exchSim
    pfBF = -pfS * stockSim
    
    interestD = np.exp(rD*matTime[-2])
    interestF = np.exp(rF*matTime[-2])

    for i in range(1,n):
        pfBD[i-1] = pfV[i-1] - pfS[i-1]*stockSim[i-1]*exchSim[i-1] - pfBF[i-1]*exchSim[i-1]
        pfV[i] = pfS[i-1]*stockSim[i]*exchSim[i] + pfBD[i-1]* interestD + pfBF[i-1]*exchSim[i]* interestF
    
    pfO = option.payoff(S=stockSim[-1], **v)
    discountedHedgeError = (pfV[-1]-pfO) * np.exp(-rD*T)
    return {'discounted hedge error' : discountedHedgeError, 
            'option payoff' : pfO, 
            'hedging pf value' : pfV[-1],
            'hedging pf path' : pfV, 
            'hedging pf S' : pfS, 
            'hedging pf BD' : pfBD,
            'hedging pf BF' : pfBF,
            'asset value': stockSim[-1]}


if __name__ == '__main__':
    T = 1
    S0=100
    mu = 0.08
    r = 0.05
    sigma=0.2
    K=105
    
    import pandas as pd
    deltas = 3.0 ** -np.arange(1, 10)
    errors = pd.DataFrame(columns=['rebalances','error'])
    delta = 1/4
    for delta in deltas:
        stockSim = sim.Simulate_GBM(T,delta,S0,r,sigma,10000)
        hedge = SimulateSimpleDeltaHedge(stockSim,binary,K,T,r,sigma)
        errors.loc[delta] = [delta ** -1,np.sqrt(np.var(hedge['discounted hedge error']))]
  
    errors.index.name = 'delta'
    
    import seaborn as sns
    import matplotlib.pyplot as plt
    sns.set_theme()
    plt.plot(stockSim[-1],hedge['hedging pf value'], 'o',markersize=0.75,color = 'black')
    plt.ylabel('pfV')
    plt.xlabel('S')
    plt.title("Hedge portfolio")
    plt.tight_layout()
    plt.show()
    
    
    
    
    sns.set_theme()
    plt.plot(errors.index,errors['error'])
    plt.xlim(0.35,0)
    plt.ylabel('discounted hedge error std')
    plt.xlabel('delta')
    plt.title("Hedge error vs rebalance times")
    plt.tight_layout()
    plt.show()

    
    #log-log
    sns.set_theme()
    plt.plot(errors['rebalances'],errors['error'])
    plt.ylabel('Rebalance per time unit')
    plt.xlabel('delta')
    plt.title("Log-Log Hedge error")
    plt.xscale('log')
    plt.yscale('log')
    plt.tight_layout()
    plt.show()
    
    from sklearn.linear_model import LinearRegression
    reg = LinearRegression().fit(X = np.log(errors['rebalances'].values).reshape(-1, 1),y = np.log(errors['error']))
    reg.coef_
    reg = LinearRegression().fit(X = np.log(errors.index.values).reshape(-1, 1),y = np.log(errors['error']))
    reg.coef_ #0.23, which means convergence order 0.23 = 1/4
    
    
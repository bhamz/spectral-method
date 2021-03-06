import numpy as np
import matplotlib.pyplot as plt
import numpy.fft as f
import numpy.random as r
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import scipy.integrate as integr8
import matplotlib.animation as animation


class spectral_method(object):
    def __init__(self,domain_length,discretization_num,t_stop,t_step):
        self.L = domain_length; self.n = discretization_num
        self.t_stop = t_stop; self.t_step = t_step
        k = (2*np.pi/self.L)*f.fftshift(np.array(range(int(-self.n/2),int(self.n/2))))
        k[0] = 10**-6; self.KX, self.KY = np.meshgrid(k,k)
        self.K_sq = self.KX**2 + self.KY**2

    def make_ICs(self,function,if_plot):
        space = np.linspace(-self.L/2,self.L/2,self.n)
        X,Y = np.meshgrid(space,space)
        Z = function(self.L,self.n,X,Y)  # all IC functions to receive this spatial info, return Z
        if if_plot:
            surf_animator(X,Y,Z).cr8_plot()
            plt.show()
        return X,Y,Z

    def spectraToReal(self,Zs_t,n):
        # brings sprectrum of Z of t from fourier to real space, puts in dim of n x n x t
        Z_t = np.empty((n,n,len(Zs_t)))
        for ii in range(len(Zs_t)):
            Z_t[:,:,ii] = np.real(f.ifft2(np.reshape(Zs_t[ii,:],(n,n))))
        return Z_t

    def integrate_spectra(self,IC_function,int_function,check_ICs):
        # takes function defined outside class and integrates its spectra
        if check_ICs:
            while check_ICs:
                XYZ = self.make_ICs(IC_function,True)
                print 'Is that neat? (y/n)'
                if_cont = raw_input(':>>')
                if if_cont[0] == 'y':
                    check_ICs = False
        else:
            XYZ = self.make_ICs(IC_function,False)

        Zs = np.reshape(f.fft2(XYZ[-1]),self.n**2,1)
        params = (self.n,self.KX,self.KY,self.K_sq)
        fn = integr8.ode(int_function).set_integrator('zvode',with_jacobian = False)
        fn.set_initial_value(Zs,0).set_f_params(*params)
        while fn.successful() and fn.t <= self.t_stop:
            fn.integrate(fn.t + self.t_step)
            Zs = np.vstack((Zs,fn.y))
        Z_t = self.spectraToReal(Zs,self.n)
        # returns the real space X and Y, and Z as a function of time
        return XYZ[0], XYZ[1], Z_t

class surf_animator(object):

    def __init__(self,X,Y,Z_t):
        # if statement allows for easy plotting of 3-d surface if input isnt made
        # to be a movie
        self.X = X; self.Y = Y; self.Z_t = Z_t
        if len(np.shape(Z_t)) == 3:
            self.Z = Z_t[:,:,0]
        else:
            self.Z = Z_t

    def cr8_plot(self):
        fig = plt.figure()
        ax = fig.gca(projection='3d')
        plot = ax.plot_surface(self.X,self.Y,self.Z,cmap=cm.coolwarm, antialiased = False, \
        rstride = 1, cstride=1, linewidth = 0)
        return ax, fig, plot,

    def cre8_movie(self,save_path,movie_fps):
        # animates 3-d array along axis 2
        def data_gen(frame):
            ax.clear()
            # ax.set_zlim3d([np.amin(self.Z_t), np.amax(self.Z_t)])
            ax.set_zlim3d([-3, 3])
            plot = ax.plot_surface(self.X,self.Y,self.Z_t[:,:,frame],cmap=cm.coolwarm, antialiased = False, \
            rstride = 1, cstride=1, linewidth = 0)
            return plot,

        ax, fig, plot = self.cr8_plot()
        ax.set_zlim3d([np.amin(self.Z)-1, np.amax(self.Z)+1])
        mov = animation.FuncAnimation(fig,data_gen,repeat = False)
        mov.save(save_path,fps = movie_fps)

def rand_vortices(L,n,X,Y):
    Z = 0*X; vort_num = 10 # empty space for
    wid = [3,2,1,2,1,5,0.1,0.5,2,0.7,2] # thats sorta random right?
    for i in range(vort_num):
        expo = -( (((X-r.randint(-L/5,L/5))**2 )/(2*wid[r.randint(len(wid))])) +\
                  (((Y-r.randint(-L/5,L/5))**2 )/(2*wid[r.randint(len(wid))])))
        Z += ((-1)**r.randint(2))*np.exp(expo) # random +/-
    return Z

nu = 0.001
def streamline(t,fz0,n,KX,KY,K_sq):
    # diff_eq for streamline voriticity function
    Zs = np.reshape(fz0,(n,n))

    psi = -Zs/K_sq
    #take partial derivatives
    psi_x = np.real(f.ifft2(psi*1j*KX))
    psi_y = np.real(f.ifft2(psi*1j*KY))
    Zx = np.real(f.ifft2(Zs*1j*KX))
    Zy = np.real(f.ifft2(Zs*1j*KY))

    W_t = np.reshape(-nu*K_sq*Zs+ f.fft2(-psi_x*Zy + psi_y*Zx),((n**2),1))
    return W_t

# make dicretization power of 2 for fft
X,Y,Z_t = spectral_method(50,128,100,0.25).integrate_spectra(rand_vortices,streamline,True)
surf_animator(X,Y,Z_t).cre8_movie('/media/sf_Downloads/Streamline_2.mp4',15)

//                             loadStore.cc
//                             --------------------

/* Date:   6-Jun-2017
   Author: M. Rheinhardt
   Description: Copier functions for the different "plates" of the halo and the full inner data cube with host-device concurrency.
                Load balance yet to be established.
*/

//C libraries
#include <stdio.h>
#include <stdlib.h>
#include <cmath>
#include <algorithm>

#define real AcReal

#include "submodule/acc-runtime/api/math_utils.h"
#include "astaroth.h"
#include "../cparam_c.h"
#include "../cdata_c.h"

const int mxy=mx*my, nxy=nx*ny;
extern int halo_xz_size[2], halo_yz_size[2];
static AcReal *halo_xz_buffer[2], *halo_yz_buffer[2]; 
extern Node node;

const int BOT=0, TOP=1, TOT=2;
int halo_widths_x[3]={nghost,nghost,2*nghost};    // bottom and top halo width and sum of them
int halo_widths_y[3]={nghost,nghost,2*nghost};
int halo_widths_z[3]={nghost,nghost,2*nghost};

void initLoadStore()
{
//printf("lperi= %d %d %d \n", lperi[0],lperi[1],lperi[2]);
        // halo widths for undivided data cube
        if (!lperi[0]){
            if (lfirst_proc_x) halo_widths_x[BOT]=nghost+1;
            if (llast_proc_x) halo_widths_x[TOP]=nghost+1;
        }
        if (!lyinyang) {
            if (!lperi[1]){
                if (lfirst_proc_y) halo_widths_y[BOT]=nghost+1;
                if (llast_proc_y) halo_widths_y[TOP]=nghost+1;
            }
            if (!lperi[2]){
                if (lfirst_proc_z) halo_widths_z[BOT]=nghost+1;
                if (llast_proc_z) halo_widths_z[TOP]=nghost+1;
            }
        }
        halo_widths_x[TOT]=halo_widths_x[BOT]+halo_widths_x[TOP];
        halo_widths_y[TOT]=halo_widths_y[BOT]+halo_widths_y[TOP];
        halo_widths_z[TOT]=halo_widths_z[BOT]+halo_widths_z[TOP];

//printf("halo_widths_x= %d %d %d\n",halo_widths_x[BOT],halo_widths_x[TOP],halo_widths_x[TOT]);
//printf("halo_widths_y= %d %d %d\n",halo_widths_y[BOT],halo_widths_y[TOP],halo_widths_x[TOT]);
//printf("halo_widths_z= %d %d %d\n",halo_widths_z[BOT],halo_widths_z[TOP],halo_widths_x[TOT]);

        // buffer for xz and yz halos in host

        for (int i=BOT; i<=TOP; i++){
            halo_xz_size[i] = mx*nz*halo_widths_y[i]*NUM_VTXBUF_HANDLES;
            halo_yz_size[i] = ny*nz*halo_widths_x[i]*NUM_VTXBUF_HANDLES;
            if (halo_xz_buffer[i]==NULL) halo_xz_buffer[i]=(AcReal*) malloc(halo_xz_size[i]*sizeof(AcReal));
            if (halo_yz_buffer[i]==NULL) halo_yz_buffer[i]=(AcReal*) malloc(halo_yz_size[i]*sizeof(AcReal));
        }
}
/****************************************************************************************************************/
void finalLoadStore()
{
        for (int i=BOT; i<=TOP; i++){
          free(halo_xz_buffer[i]);
          free(halo_yz_buffer[i]);
        }
}
/****************************************************************************************************************/
void loadOuterFront(AcMesh& mesh, Stream stream)
{
        int3 src={0,0,0};
        int num_vertices=mxy*halo_widths_z[BOT];
        acNodeLoadMeshWithOffset(node, stream, mesh, src, src, num_vertices);

//printf("front:num_vertices= %d \n",num_vertices);
        //!!!cudaHostRegister(mesh, size, cudaHostRegisterDefault);    // time-critical!
}

void loadOuterBack(AcMesh& mesh, Stream stream)
{
        int3 src={0,0,mz-halo_widths_z[TOP]};      // index from m2-halo_widths_z[TOP] to m2-1
        int num_vertices=mxy*halo_widths_z[TOP];
        acNodeLoadMeshWithOffset(node, stream, mesh, src, src, num_vertices);

//printf("back:num_vertices= %d \n",num_vertices);
        //!!!cudaHostRegister(mesh, size, cudaHostRegisterDefault);    // time-critical!
}
 
void loadOuterBot(AcMesh& mesh, Stream stream)
{
        int3 start=(int3){0, 0,                    halo_widths_z[BOT]};
        int3 end  =(int3){mx,halo_widths_y[BOT],mz-halo_widths_z[TOP]};  //end is exclusive

        acNodeLoadPlateXcomp(node, stream, start, end, &mesh, halo_xz_buffer[BOT], AC_XZ);
}

void loadOuterTop(AcMesh& mesh, Stream stream)
{
        int3 start=(int3){0, my-halo_widths_y[TOP],   halo_widths_z[BOT]};
        int3 end  =(int3){mx,my,                   mz-halo_widths_z[TOP]};  //end is exclusive
//printf("loadOuterTop: %d %d %d %d %d %d \n", start.x,end.x,start.y,end.y,start.z,end.z);
        acNodeLoadPlateXcomp(node, stream, start, end, &mesh, halo_xz_buffer[TOP], AC_XZ);
}

void loadOuterLeft(AcMesh& mesh, Stream stream)
{
    int3 start=(int3){0,                      halo_widths_y[BOT],     halo_widths_z[BOT]};
    int3 end  =(int3){halo_widths_x[BOT]-1,my-halo_widths_y[TOP]-1,mz-halo_widths_z[TOP]-1}+1;  //end is exclusive

    acNodeLoadPlate(node, stream, start, end, &mesh, halo_yz_buffer[BOT], AC_YZ);
}

void loadOuterRight(AcMesh& mesh, Stream stream)
{
    int3 start=(int3){mx-halo_widths_x[TOP],   halo_widths_y[BOT],     halo_widths_z[BOT]};
    int3 end  =(int3){mx-1,                 my-halo_widths_y[TOP]-1,mz-halo_widths_z[TOP]-1}+1; //end is exclusive

    acNodeLoadPlate(node, stream, start, end, &mesh, halo_yz_buffer[TOP], AC_YZ);
}

void loadOuterHalos(AcMesh& mesh)
{
    loadOuterFront(mesh,STREAM_DEFAULT);
    loadOuterBack(mesh,STREAM_DEFAULT);
    loadOuterTop(mesh,STREAM_DEFAULT);
    loadOuterBot(mesh,STREAM_DEFAULT);
    loadOuterLeft(mesh,STREAM_DEFAULT);
    loadOuterRight(mesh,STREAM_DEFAULT);
}

void storeInnerFront(AcMesh& mesh, Stream stream)
{
        int3 start=(int3){l1,m1,n1}-1;
        int3 end  =(int3){l2,m2,n1+halo_widths_z[BOT]-1}-1+1;   //end is exclusive

//printf("storeInnerFront: start,end= %d %d %d %d %d %d \n",start.x, end.x,start.y, end.y,start.z, end.z);
        acNodeStoreIXYPlate(node, stream, start, end, &mesh, BOT);
        //acNodeStorePlate(node, stream, start, end, &mesh, halo_xy_buffer, AC_XY);
}

void storeInnerBack(AcMesh& mesh, Stream stream)
{
        int3 start=(int3){l1,m1,n2-halo_widths_z[TOP]+1}-1;
        int3 end  =(int3){l2,m2,n2                     }-1+1;    //end is exclusive
//printf("storeInnerBack: start,end= %d %d %d %d %d %d \n",start.x, end.x,start.y, end.y,start.z, end.z);
        acNodeStoreIXYPlate(node, stream, start, end, &mesh, TOP);
        //acNodeStorePlate(node, stream, start, end, &mesh, halo_xy_buffer, AC_XY);
}

void storeInnerBot(AcMesh& mesh, Stream stream)
{
        int3 start=(int3){l1,m1,n1+halo_widths_z[BOT]}-1;
        int3 end=(int3){l2,m1+halo_widths_y[BOT]-1,n2-halo_widths_z[TOP]}-1+1;   //end is exclusive

        acNodeStorePlate(node, stream, start, end, &mesh, halo_xz_buffer[BOT], AC_XZ);
}

void storeInnerTop(AcMesh& mesh, Stream stream)
{
        int3 start=(int3){l1,m2-halo_widths_y[TOP]+1,n1+halo_widths_z[BOT]}-1;
        int3 end=(int3){l2,m2,n2-halo_widths_z[TOP]}-1+1;    //end is exclusive

        acNodeStorePlate(node, stream, start, end, &mesh, halo_xz_buffer[TOP], AC_XZ);
}

void storeInnerLeft(AcMesh& mesh, Stream stream)
{
    int3 start=(int3){l1,                     m1+halo_widths_y[BOT],n1+halo_widths_z[BOT]}-1;
    int3 end  =(int3){l1+halo_widths_x[BOT]-1,m2-halo_widths_y[TOP],n2-halo_widths_z[TOP]}-1+1;  //end is exclusive

    acNodeStorePlate(node, stream, start, end, &mesh, halo_yz_buffer[BOT], AC_YZ);
}

void storeInnerRight(AcMesh& mesh, Stream stream)
{
    int3 start=(int3){l2-halo_widths_x[TOP]+1,m1+halo_widths_y[BOT],n1+halo_widths_z[BOT]}-1;
    int3 end  =(int3){l2,                     m2-halo_widths_y[TOP],n2-halo_widths_z[TOP]}-1+1; //end is exclusive

    acNodeStorePlate(node, stream, start, end, &mesh, halo_yz_buffer[TOP], AC_YZ);
}

void storeInnerHalos(AcMesh& mesh)
{
    storeInnerLeft(mesh,STREAM_4);
    storeInnerRight(mesh,STREAM_5);
    storeInnerBot(mesh,STREAM_2);
    storeInnerTop(mesh,STREAM_3);
    storeInnerFront(mesh,STREAM_6);
    storeInnerBack(mesh,STREAM_1);
}

